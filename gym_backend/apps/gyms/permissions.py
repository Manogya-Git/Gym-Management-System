from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Gym, GymStaff


def ensure_gym_owner(gym_staff):
    """Raise 403 if the active gym staff member is not an owner."""
    if gym_staff.role != GymStaff.Role.OWNER:
        raise PermissionDenied("Only gym owners can perform this action.")


class IsGymOwnerOrReadOnly(BasePermission):
    """Allow active gym staff to read, and only owners to modify."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        gym = obj if isinstance(obj, Gym) else obj.gym
        return GymStaff.objects.filter(
            gym=gym,
            user=request.user,
            role=GymStaff.Role.OWNER,
            is_active=True,
        ).exists()
