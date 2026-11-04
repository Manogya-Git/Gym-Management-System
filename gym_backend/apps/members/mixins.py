from django.shortcuts import get_object_or_404
from apps.gyms.models import GymStaff
from apps.members.models import Member


class GymStaffRequiredMixin:
    def get_gym_staff(self):
        return get_object_or_404(
            GymStaff,
            gym_id=self.kwargs["gym_id"],
            user=self.request.user,
            is_active=True
        )

class ActiveMemberQuerySetMixin(GymStaffRequiredMixin):
    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        return Member.objects.filter(
            gym=gym_staff.gym,
            deleted_at__isnull=True
        )

class DeletedMemberQuerySetMixin(GymStaffRequiredMixin):
    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        return Member.objects.filter(
            gym=gym_staff.gym,
            deleted_at__isnull=False
        ) 
