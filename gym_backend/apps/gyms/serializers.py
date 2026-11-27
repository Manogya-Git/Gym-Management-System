from rest_framework import serializers

from .models import Gym, GymStaff


def validate_owner_retention(instance, *, next_role, next_is_active):
    """Ensure the primary gym owner or last active owner cannot be removed."""
    is_losing_owner_access = next_role != GymStaff.Role.OWNER or not next_is_active
    if not is_losing_owner_access:
        return

    if instance.user_id == instance.gym.owner_id:
        raise serializers.ValidationError(
            "The primary gym owner cannot be demoted or deactivated."
        )

    other_active_owners = GymStaff.objects.filter(
        gym=instance.gym,
        role=GymStaff.Role.OWNER,
        is_active=True,
    ).exclude(pk=instance.pk)
    if not other_active_owners.exists():
        raise serializers.ValidationError(
            "A gym must retain at least one active owner."
        )


class GymSerializer(serializers.ModelSerializer):
    """Serializer for listing, creating, and retrieving gyms."""

    class Meta:
        model = Gym
        fields = [
            "id",
            "name",
            "status",
            "timezone",
            "currency",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class GymUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating gym settings and status."""

    class Meta:
        model = Gym
        fields = [
            "id",
            "name",
            "status",
            "timezone",
            "currency",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GymStaffSerializer(serializers.ModelSerializer):
    """Serializer for listing, retrieving, and adding gym staff members."""

    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = GymStaff
        fields = [
            "id",
            "user",
            "email",
            "first_name",
            "last_name",
            "gym",
            "role",
            "is_active",
            "hired_on",
        ]
        read_only_fields = ["id", "gym", "hired_on"]

    def validate(self, attrs):
        if self.instance is None:
            gym_id = int(self.context["request"].parser_context["kwargs"]["gym_id"])
            user = attrs.get("user")
            if user is not None and GymStaff.objects.filter(
                gym_id=gym_id, user=user
            ).exists():
                raise serializers.ValidationError(
                    "This user is already associated with this gym."
                )
        return attrs


class GymStaffUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a gym staff member's role or active status."""

    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = GymStaff
        fields = [
            "id",
            "user",
            "email",
            "first_name",
            "last_name",
            "gym",
            "role",
            "is_active",
            "hired_on",
        ]
        read_only_fields = ["id", "user", "gym", "hired_on"]

    def validate(self, attrs):
        next_role = attrs.get("role", self.instance.role)
        next_is_active = attrs.get("is_active", self.instance.is_active)
        validate_owner_retention(
            self.instance,
            next_role=next_role,
            next_is_active=next_is_active,
        )
        return attrs
