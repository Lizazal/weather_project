from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache
from django.contrib.auth import login
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CityQueryStats, SearchHistory
from .forms import RegisterForm
from .serializers import SearchHistorySerializer
from .utils import search_nominatim, get_city_coordinates, fetch_weather
from typing import Optional


@require_GET
def city_redirect(request: HttpRequest) -> HttpResponse:
    """
    Для редиректа: при переходе по ссылке с городом делает редирект на главную страницу
    """
    city_name = request.GET.get('name')
    if city_name:
        request.session['city_redirect_name'] = city_name
    return redirect('index')


def index(request: HttpRequest) -> HttpResponse:
    """
    Работает как на GET, так и POST-запросах
    Сохраняет историю поиска, ведёт учёт статистики, кэширует данные
    """
    weather_data = {}
    error = None
    normalized_name: Optional[str] = None

    # Обработка перехода по ссылке с городом
    redirect_city = request.session.pop('city_redirect_name', None)
    if redirect_city:
        request.method = 'POST'
        request.POST = request.POST.copy()
        request.POST['city'] = redirect_city

    if request.method == 'POST':
        city_input = request.POST.get('city')  # как название города вводит пользователь
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        display_name = request.POST.get('display_name')  # как название города отображается в Nominatim

        # Определение координат и нормализованного названия города
        # Если есть координаты - будем получать погоду по ним
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
                # Если есть имя из Nominatim - используем его
                normalized_name = display_name or city_input
            except ValueError:
                lat = lon = None
                normalized_name = city_input
        # Иначе будем сначала получать координаты
        else:
            data = search_nominatim(city_input, limit=1)
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                normalized_name = data[0]['display_name']
            else:
                error = 'Город не найден.'
                normalized_name = city_input

        # Получение прогноза погоды если город найден
        if lat and lon and not error:
            try:
                weather_data = fetch_weather(lat, lon)
                if not request.user.is_authenticated:
                    weather_data['normalized_name'] = normalized_name
                    cache.set('last_weather_data', weather_data, timeout=3600)
            except Exception as e:
                error = f'Ошибка при запросе погоды: {e}'

        # Сбор статистики, сохранение истории для зарегестрированных пользователей
        if normalized_name:
            stats, _ = CityQueryStats.objects.get_or_create(
                user_input=city_input,
                normalized_name=normalized_name
            )
            stats.count += 1
            stats.save()

            if request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    query=city_input,
                    display_name=normalized_name
                )
            else:
                history = request.session.get('search_history', [])
                if normalized_name not in history:
                    history.append(normalized_name)
                    # Оставляем в истории 5 последних запросов
                    request.session['search_history'] = history[-5:]

    # GET-запрос
    else:
        if request.user.is_authenticated:
            last = SearchHistory.objects.filter(user=request.user).order_by('-searched_at').first()
            if last:
                normalized_name = last.display_name
                lat, lon = get_city_coordinates(last.query)
                if lat and lon:
                    try:
                        weather_data = fetch_weather(lat, lon)
                    except Exception as e:
                        error = f'Ошибка при загрузке погоды: {e}'
        else:
            cached = cache.get('last_weather_data') or {}
            weather_data = cached
            normalized_name = cached.get('normalized_name')

    history = request.session.get('search_history', []) if not request.user.is_authenticated else [
        h.display_name for h in SearchHistory.objects.filter(user=request.user).order_by('-searched_at')[:5]
    ]

    return render(request, 'weather/index.html', {
        'weather': weather_data,
        'error': error,
        'history': history,
        'city_name': normalized_name
    })


def autocomplete_city(request: HttpRequest) -> JsonResponse:
    """
    Обработка AJAX-запроса автодополнения городов через Nominatim
    """
    query = request.GET.get('term', '')
    suggestions = []
    if query:
        # До 5 предложений автодополнения
        data = search_nominatim(query, limit=5)
        for place in data:
            suggestions.append({
                'name': place['display_name'],
                'lat': float(place['lat']),
                'lon': float(place['lon'])
            })
    return JsonResponse({'suggestions': suggestions})


class CityStatsView(APIView):
    """
    Количество запросов по городам
    """

    def get(self, request: HttpRequest) -> Response:
        stats = (
            CityQueryStats.objects
            .values('normalized_name')
            .annotate(total=Sum('count'))
            .order_by('-total')
        )
        return Response(stats)


def register(request: HttpRequest) -> HttpResponse:
    """
    Стандартная регистрация пользователя
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


class UserSearchHistoryView(APIView):
    """
    История запросов текущего пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> Response:
        history = SearchHistory.objects.filter(user=request.user).order_by('-searched_at')
        serializer = SearchHistorySerializer(history, many=True)
        return Response(serializer.data)
