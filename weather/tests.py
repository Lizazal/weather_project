from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import SearchHistory, CityQueryStats


class WeatherAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.index_url = reverse('index')
        self.autocomplete_url = reverse('autocomplete_city')
        self.register_url = reverse('register')
        self.history_url = reverse('user_search_history')
        self.stats_url = reverse('city_stats_api')

    def test_index_page_loads(self):
        """
        Загрузка главной страницы
        """
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/index.html')

    def test_autocomplete_returns_json(self):
        """
        Автодополнения возвращают JSON
        """
        response = self.client.get(self.autocomplete_url, {'term': 'Moscow'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])

    def test_registration(self):
        """
        Регистрируем пользователя
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@gmail.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertRedirects(response, self.index_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_search_history_requires_auth(self):
        """
        history/ требует аутентификацию
        """
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 403)

    def test_search_history_if_authenticated(self):
        """
        Вошедший пользователь получает свою историю поиска
        """
        self.client.login(username='testuser', password='testpass')
        SearchHistory.objects.create(user=self.user, query='Moscow', display_name='Moscow, Russia')
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["query"], "Moscow")

    def test_stats(self):
        """
        Статистика выдаёт информацию по городам
        """
        CityQueryStats.objects.create(user_input='Moscow', normalized_name='Moscow, Russia', count=5)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Moscow', str(response.content))
