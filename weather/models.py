from django.db import models
from django.contrib.auth.models import User


class CityQueryStats(models.Model):
    user_input = models.CharField(max_length=255, unique=True)  # город как ввёл пользователь
    normalized_name = models.CharField(max_length=255)  # город из Nominatim
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user_input', 'normalized_name')

    def __str__(self):
        return f'{self.user_input}, {self.normalized_name}: {self.count}'


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.query} ({self.searched_at})'
