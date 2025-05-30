from rest_framework import serializers
from .models import CityQueryStats, SearchHistory


class CityQueryStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityQueryStats
        fields = ['user_input', 'normalized_name', 'count']


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['query', 'display_name', 'searched_at']
