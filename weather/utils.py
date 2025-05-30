import requests
from django.core.cache import cache
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any


# Погодные коды согласно API Open-Meteo:
# https://open-meteo.com/en/docs#api-formats
WEATHER_CODES: dict[int, str] = {
    0: 'Ясно',
    1: 'Преимущественно ясно',
    2: 'Переменная облачность',
    3: 'Пасмурно',
    45: 'Туман',
    48: 'Иней',
    51: 'Морось: лёгкая',
    53: 'Морось: умеренная',
    55: 'Морось: сильная',
    61: 'Дождь: слабый',
    63: 'Дождь: умеренный',
    65: 'Дождь: сильный',
    66: 'Ледяной дождь: слабый',
    67: 'Ледяной дождь: сильный',
    71: 'Снегопад: слабый',
    73: 'Снегопад: умеренный',
    75: 'Снегопад: сильный',
    77: 'Град',
    80: 'Кратковременный дождь: слабый',
    81: 'Кратковременный дождь: умеренный',
    82: 'Кратковременный дождь: сильный',
    85: 'Кратковременный снег: слабый',
    86: 'Кратковременный снег: сильный',
    95: 'Гроза',
    96: 'Гроза: с мелким градом',
    99: 'Гроза: с крупным градом',
}


def search_nominatim(query: str, limit: int = 1) -> List[Dict[str, Any]]:
    """
    Ищет координаты города через Nominatim API
    Кэширует результат на час, чтобы избежать частых обращений -> повысить скорость
    """
    query_key = query.strip().lower()
    cache_key = f'coords:{query_key}:{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': query,
        'format': 'json',
        'limit': limit
    }
    headers = {
        'User-Agent': 'weather_project-demo (liza.rzal@gmail.com)'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        if data:
            cache.set(cache_key, data, timeout=3600)
        return data
    except requests.RequestException:
        return []


def get_city_coordinates(city_name: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Возвращает координаты (lat, lon) для названия города
    """
    data = search_nominatim(city_name, limit=1)
    if data:
        try:
            return float(data[0]['lat']), float(data[0]['lon'])
        except (KeyError, ValueError):
            pass
    return None, None


def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Получает текущую погоду и прогноз на 24 часа по координатам
    """
    url = (
        f'https://api.open-meteo.com/v1/forecast?'
        f'latitude={lat}&longitude={lon}'
        '&current_weather=true'
        '&hourly=temperature_2m,weathercode,precipitation,wind_speed_10m'
        '&timezone=auto'
    )

    response = requests.get(url, timeout=5)
    json_data = response.json()

    current_weather = json_data.get('current_weather', {})
    hourly_data = json_data.get('hourly', {})

    # Получаем списки показателей по времени
    time_list = hourly_data.get('time', [])
    temp_list = hourly_data.get('temperature_2m', [])
    precip_list = hourly_data.get('precipitation', [])
    wind_list = hourly_data.get('wind_speed_10m', [])
    weathercode_list = hourly_data.get('weathercode', [])

    # Находим индекс текущего часа
    now_str = datetime.now().strftime('%Y-%m-%dT%H:00')
    try:
        start_idx = time_list.index(now_str)
    except ValueError:
        start_idx = 0  # если текущего часа нет, начинаем с начала

    # Формируем прогноз на 24 часа
    hourly_forecast = []
    for i in range(start_idx, min(start_idx + 24, len(time_list))):
        hourly_forecast.append({
            'time': datetime.fromisoformat(time_list[i]),
            'temp': temp_list[i],
            'precip': precip_list[i],
            'wind': wind_list[i],
            'code': WEATHER_CODES.get(weathercode_list[i], 'Неизвестно'),
        })
    return {
        'current': current_weather,
        'hourly': hourly_forecast
    }
