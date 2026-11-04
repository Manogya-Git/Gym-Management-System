from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import MemberSerializer
from .models import Member
from .mixins import ActiveMemberQuerySetMixin, DeletedMemberQuerySetMixin


class MemberCreateAPIView( ActiveMemberQuerySetMixin, generics.ListCreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        gym_staff = self.get_gym_staff()
        serializer.save(gym=gym_staff.gym)


class MemberDetailAPIView(
    ActiveMemberQuerySetMixin, 
    generics.RetrieveUpdateDestroyAPIView
    ):
    serializer_class = MemberSerializer 
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

class MemberDeleteAPIView(
    ActiveMemberQuerySetMixin,
    generics.DestroyAPIView
    ):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])

class DeletedMemberListAPIView(
    DeletedMemberQuerySetMixin,
    generics.ListAPIView
):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

class MemberRestoreAPIView(
    DeletedMemberQuerySetMixin,
    generics.UpdateAPIView
):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "id"

    def perform_update(self, serializer):
        serializer.instance.deleted_at = None
        serializer.instance.save(update_fields=["deleted_at"])