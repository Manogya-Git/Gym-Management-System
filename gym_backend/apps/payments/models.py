from django.db import models
from django.utils import timezone


class Invoice(models.Model):
	class Status(models.TextChoices):
		UNPAID = "UNPAID", "Unpaid"
		PARTIALLY_PAID = "PARTIALLY_PAID", "Partially paid"
		PAID = "PAID", "Paid"
		VOID = "VOID", "Void"

	gym = models.ForeignKey("gyms.Gym", on_delete=models.PROTECT, related_name="invoices")
	number = models.CharField(max_length=30)
	member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="invoices")
	subscription = models.OneToOneField(
		"subscriptions.Subscription",
		on_delete=models.PROTECT,
		related_name="invoice",
	)
	total = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
	issued_on = models.DateField(default=timezone.localdate)
	due_on = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["gym", "number"],
				name="unique_invoice_number_per_gym",
			),
		]

	def __str__(self):
		return f"Invoice {self.number} - {self.total} ({self.status})"


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
		CANCELLED = "cancelled", "Cancelled"

	gym = models.ForeignKey("gyms.Gym", on_delete=models.PROTECT, related_name="payments")
	member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="payments")
	subscription = models.ForeignKey(
		"subscriptions.Subscription",
		on_delete=models.PROTECT,
		related_name="payments",
	)
	invoice = models.ForeignKey(
		Invoice,
		on_delete=models.PROTECT,
		related_name="payments",
		null=True,
		blank=True,
	)
	plan = models.ForeignKey(
    "plans.Plan",
    on_delete=models.PROTECT,
    related_name="payments",
        null=True,
    blank=True,
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

	
