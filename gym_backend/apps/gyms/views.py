from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Gym, GymStaff
from .permissions import IsGymOwnerOrReadOnly, ensure_gym_owner
from .serializers import (
    GymSerializer,
    GymStaffSerializer,
    GymStaffUpdateSerializer,
    GymUpdateSerializer,
    validate_owner_retention,
)
from .services import create_gym


class GymListCreateAPIView(generics.ListCreateAPIView):
    """List gyms where the user is active staff, or create a new gym."""

    serializer_class = GymSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Gym.objects.filter(
            staff_members__user=self.request.user,
            staff_members__is_active=True,
        ).distinct()

    def perform_create(self, serializer):
        gym = create_gym(
            owner=self.request.user,
            **serializer.validated_data,
        )
        serializer.instance = gym


class GymDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a gym that the user belongs to."""

    permission_classes = [IsAuthenticated, IsGymOwnerOrReadOnly]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return GymUpdateSerializer
        return GymSerializer

    def get_queryset(self):
        return Gym.objects.filter(
            staff_members__user=self.request.user,
            staff_members__is_active=True,
        ).distinct()


class GymStaffListCreateAPIView(generics.ListCreateAPIView):
    """List staff members of a gym or assign a new staff member (owner only)."""

    serializer_class = GymStaffSerializer
    permission_classes = [IsAuthenticated]

    def get_gym_staff(self):
        return get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True,
        )

    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        queryset = GymStaff.objects.filter(gym=gym_staff.gym).select_related("user")

        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            normalized = is_active.strip().lower()
            if normalized in ("true", "1"):
                queryset = queryset.filter(is_active=True)
            elif normalized in ("false", "0"):
                queryset = queryset.filter(is_active=False)

        return queryset

    def create(self, request, *args, **kwargs):
        gym_staff = self.get_gym_staff()
        ensure_gym_owner(gym_staff)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        gym_staff = self.get_gym_staff()
        serializer.save(gym=gym_staff.gym)


class GymStaffDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or deactivate a gym staff member."""

    permission_classes = [IsAuthenticated, IsGymOwnerOrReadOnly]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return GymStaffUpdateSerializer
        return GymStaffSerializer

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True,
        )
        return GymStaff.objects.filter(gym=gym_staff.gym).select_related("user")

    def perform_destroy(self, instance):
        validate_owner_retention(
            instance,
            next_role=instance.role,
            next_is_active=False,
        )
        instance.is_active = False
        instance.save(update_fields=["is_active"])
