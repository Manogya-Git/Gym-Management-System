from django.conf import settings
from django.db import models

# Create your models here.
class Gym(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gyms",
    )

class GymStaff(models.Model):
    class roles(models.TextChoices):
        OWNER = "owner", "Owner"
        STAFF = "staff", "Staff"
        TRAINER = "trainer","Trainer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="Users")
    gym = models.ForeignKey(Gym,on_delete=models.CASCADE)
    role = models.CharField(
        max_length=8,
        choices=roles.choices
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user',
                'gym'],
                name='unique_user_gym_role'
            )
        ]