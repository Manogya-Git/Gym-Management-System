from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment
		fields = [
			"id",
			"gym",
			"member",
			"subscription",
			"amount",
			"payment_method",
			"status",
			"transaction_reference",
			"paid_at",
			"created_at",
			"updated_at",
		]
		read_only_fields = [
			"id",
			"gym",
			"amount",
			"status",
			"transaction_reference",
			"paid_at",
			"created_at",
			"updated_at",
		]

class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment
		fields = ['status']

	def validate_status(self, value):
		status = self.instance.status

		if not (
			(status == Payment.Status.PENDING and value == Payment.Status.COMPLETED)
			or
			(status == Payment.Status.COMPLETED and value == Payment.Status.REFUNDED)
		):
			raise serializers.ValidationError(
				"This payment status transition is not allowed."
			)

		return value


