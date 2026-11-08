from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 
            'gym',
            'name', 
            'description', 
            'price', 
            'duration_days', 
            'is_active', 
            'created_at', 
            'updated_at']
        read_only_fields = [
            "id",
            'gym',
            "is_active",
            "created_at",
            "updated_at",
        ]
