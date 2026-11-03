from django.conf import settings
from django.db import models
from django.utils.text import slugify

# Create your models here.
class Gym(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="gyms",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "gym"
            self.slug = base_slug
            suffix = 2
            while type(self).objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{suffix}"
                suffix += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class GymStaff(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        STAFF = "staff", "Staff"
        TRAINER = "trainer", "Trainer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gym_memberships")
    gym = models.ForeignKey(Gym,on_delete=models.CASCADE)
    role = models.CharField(
        max_length=8,
        choices=Role.choices
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

    def __str__(self):
        return f"{self.user} - {self.gym} ({self.get_role_display()})"