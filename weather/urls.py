from django.urls import path
from . import views

urlpatterns = [
    # Главная страница - форма поиска и отображение погоды
    path('', views.index, name='index'),
    # Автодополнение города
    path('autocomplete/', views.autocomplete_city, name='autocomplete_city'),
    # Сколько раз вводили какой город
    path('stats/', views.CityStatsView.as_view(), name='city_stats_api'),
    # Регистрация нового пользователя
    path('register/', views.register, name='register'),
    # История поиска текущего пользователя
    path('history/', views.UserSearchHistoryView.as_view(), name='user_search_history'),
    # Редирект с подстановкой города
    path('city/', views.city_redirect, name='city_redirect'),
]
