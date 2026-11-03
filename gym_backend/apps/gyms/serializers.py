from rest_framework import serializers

from .models import Gym


class GymSerializer(serializers.ModelSerializer):

    class Meta:
        model = Gym
        fields = [
            "id",
            "name",
            "status",
            "timezone",
            "currency",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]