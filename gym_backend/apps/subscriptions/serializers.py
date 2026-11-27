
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Subscription


def _validate_no_other_active_subscription(*, gym_id, member, exclude_pk=None):
    """Ensure a member has at most one active non-expired subscription per gym."""
    existing = Subscription.objects.filter(
        gym_id=gym_id,
        member=member,
        status=Subscription.Status.ACTIVE,
        end_date__gte=timezone.localdate(),
    )
    if exclude_pk is not None:
        existing = existing.exclude(pk=exclude_pk)
    if existing.exists():
        raise serializers.ValidationError(
            "This member already has an active subscription."
        )


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = [
            "id",
            "member",
            "plan",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
            "price",
        ]

        read_only_fields = [
            "id",
            "gym",
            "end_date",
            "price",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):

        if self.instance:
            member = data.get("member", self.instance.member)
            status = data.get("status", self.instance.status)
            plan = data.get("plan", self.instance.plan)
        else:
            member = data.get("member")
            status = data.get("status", Subscription.Status.ACTIVE)
            plan = data.get("plan")

        if plan is not None and not plan.is_active:
            raise serializers.ValidationError(
                "Cannot use an inactive plan."
            )

        gym = int(self.context["request"].parser_context["kwargs"]["gym_id"])

        # Check whether member belongs to this gym.
        if member is not None and member.gym_id != gym:
            raise serializers.ValidationError(
                "This member does not belong to the selected gym."
            )

        # Check whether plan belongs to this gym.
        if plan is not None and plan.gym_id != gym:
            raise serializers.ValidationError(
                "This plan does not belong to the selected gym."
            )

        # Prevent multiple active subscriptions.
        if status == Subscription.Status.ACTIVE:
            _validate_no_other_active_subscription(
                gym_id=gym,
                member=member,
                exclude_pk=self.instance.pk if self.instance else None,
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        plan = validated_data["plan"]
        start_date = validated_data["start_date"]
        member = validated_data["member"]
        today = timezone.localdate()

        end_date = start_date + timedelta(days=plan.duration_days)

        Subscription.objects.filter(
            member=member,
            status=Subscription.Status.ACTIVE,
            end_date__lt=today,
        ).update(status=Subscription.Status.EXPIRED)

        subscription = Subscription.objects.create(
            **validated_data,
            end_date=end_date,
            price=plan.price
        )

        return subscription


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating mutable subscription fields such as end_date or status."""

    class Meta:
        model = Subscription
        fields = [
            "id",
            "member",
            "plan",
            "start_date",
            "end_date",
            "status",
            "price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "member",
            "plan",
            "start_date",
            "price",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        end_date = attrs.get("end_date", self.instance.end_date)
        status = attrs.get("status", self.instance.status)

        if end_date < self.instance.start_date:
            raise serializers.ValidationError(
                "End date cannot be earlier than start date."
            )

        if status == Subscription.Status.ACTIVE:
            _validate_no_other_active_subscription(
                gym_id=self.instance.gym_id,
                member=self.instance.member,
                exclude_pk=self.instance.pk,
            )

        return attrs
