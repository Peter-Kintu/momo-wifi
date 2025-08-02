from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'duration_minutes', 'duration_hours']

    def get_duration_hours(self, obj):
        return round(obj.duration_minutes / 60, 2)
