from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.gyms.models import GymStaff
from .models import Plan
from .serializers import PlanSerializer

class PlanListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_gym_staff(self):
        return get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        return Plan.objects.filter(gym=gym_staff.gym,
    is_active=True)

    def perform_create(self, serializer):
        gym_staff = self.get_gym_staff()
        serializer.save(gym=gym_staff.gym)

class PlanDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

        return Plan.objects.filter(gym=gym_staff.gym,
                                   is_active=True)

class PlanDeleteAPIView(generics.DestroyAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

        return Plan.objects.filter(
            gym=gym_staff.gym,
            is_active=True
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class InactivePlanListAPIView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

        return Plan.objects.filter(
            gym=gym_staff.gym,
            is_active=False
        )

class PlanRestoreAPIView(generics.UpdateAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

        return Plan.objects.filter(
            gym=gym_staff.gym,
            is_active=False
        )

    def perform_update(self, serializer):
        serializer.instance.is_active = True
        serializer.instance.save(update_fields=["is_active"])