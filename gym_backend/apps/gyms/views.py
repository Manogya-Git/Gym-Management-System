from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import GymSerializer
from .services import create_gym


class GymCreateAPIView(generics.CreateAPIView):
    serializer_class = GymSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        gym = create_gym(
        owner=self.request.user,
        **serializer.validated_data
    )

        serializer.instance = gym