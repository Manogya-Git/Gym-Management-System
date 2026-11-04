from django.db import models
from apps.gyms.models import Gym


class Member(models.Model):
	gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="members")
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	email = models.EmailField()
	phone = models.CharField(max_length=20)
	date_of_birth = models.DateField()
	is_active = models.BooleanField(default=True)
	deleted_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["gym", "email"], name="unique_member_email_per_gym"),
		]

	def __str__(self):
		return f"{self.first_name} {self.last_name}"
