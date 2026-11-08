from django.db import models

from apps.gyms.models import Gym


class Plan(models.Model):
    class Name(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        YEARLY = "YEARLY", "Yearly"

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="plans")
    name = models.CharField(max_length=20, choices=Name.choices)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.gym.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gym","name"],
                name="unique_plan_per_gym"
            )
        ]
