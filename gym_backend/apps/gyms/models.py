from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Gym(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(max_length=255)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_gyms"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    timezone = models.CharField(
        max_length=50,
        default="Asia/Kathmandu"
    )

    currency = models.CharField(
        max_length=3,
        default="NPR"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class GymStaff(models.Model):

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        STAFF = "STAFF", "Staff"
        TRAINER = "TRAINER", "Trainer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gym_memberships"
    )

    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="staff_members"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices
    )

    is_active = models.BooleanField(default=True)

    hired_on = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "gym"],
                name="unique_user_per_gym"
            )
        ]

        indexes = [
            models.Index(
                fields=["user", "is_active"],
                name="gymstaff_user_active_idx"
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.gym.name} ({self.role})"