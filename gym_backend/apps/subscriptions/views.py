from datetime import timezone

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.gyms.models import GymStaff
from .models import Subscription
from .serializers import SubscriptionSerializer
from rest_framework.exceptions import ValidationError
from django.utils import timezone


class SubscriptionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_gym_staff(self):
        return get_object_or_404(
            GymStaff,
            gym_id = self.kwargs['gym_id'],
            user = self.request.user,
            is_active = True
        )

    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        return Subscription.objects.filter(
            gym = gym_staff.gym
        )

    def perform_create(self,serializer):
        gym_staff = self.get_gym_staff()
        serializer.save(gym = gym_staff.gym)

class SubscriptionDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id = self.kwargs['gym_id'],
            user = self.request.user,
            is_active = True
        )

        return Subscription.objects.filter(gym = gym_staff.gym)

class SubscriptionCancelAPIView(generics.DestroyAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id = self.kwargs['gym_id'],
            user = self.request.user,
            is_active = True
        )

        return Subscription.objects.filter(
            gym = gym_staff.gym,
            status=Subscription.Status.ACTIVE
        )

    def perform_destroy(self, instance):
        if instance.status == Subscription.Status.CANCELLED:
            raise ValidationError("Subscription is already cancelled.")
        instance.status = Subscription.Status.CANCELLED
        instance.save()

class CancelledSubscriptionListAPIView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

        return Subscription.objects.filter(
            gym=gym_staff.gym,
            status=Subscription.Status.CANCELLED
        )

class SubscriptionRestoreAPIView(generics.UpdateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        gym_staff = get_object_or_404(
            GymStaff,
            gym_id=self.kwargs['gym_id'],
            user = self.request.user,
            is_active = True
        )
        return Subscription.objects.filter(
                    gym=gym_staff.gym,
                    status=Subscription.Status.CANCELLED
                )
    def perform_update(self, serializer):
        if serializer.instance.end_date <= timezone.localdate():
            raise ValidationError("You cannot restore this subscription")
        serializer.instance.status = Subscription.Status.ACTIVE
        serializer.save()

    
    





