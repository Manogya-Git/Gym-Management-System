from django.db import models


class Payment(models.Model):
	class PaymentMethod(models.TextChoices):
		CASH = "cash", "Cash"
		ESEWA = "esewa", "eSewa"
		KHALTI = "khalti", "Khalti"
		OTHER = "other", "Other"

	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		COMPLETED = "completed", "Completed"
		FAILED = "failed", "Failed"
		REFUNDED = "refunded", "Refunded"

	gym = models.ForeignKey("gyms.Gym", on_delete=models.PROTECT, related_name="payments")
	member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="payments")
	subscription = models.ForeignKey(
		"subscriptions.Subscription",
		on_delete=models.PROTECT,
		related_name="payments",
	)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	transaction_reference = models.CharField(max_length=255, blank=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Payment {self.pk} - {self.amount} ({self.status})"
