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

