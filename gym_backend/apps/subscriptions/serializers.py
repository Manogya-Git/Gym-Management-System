
from rest_framework import serializers

from .models import Subscription


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
        ]
        read_only_fields = [
            "id",
            "gym",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        if self.instance:
            member = data.get("member", self.instance.member)
            status = data.get("status", self.instance.status)
        else:
            member = data.get("member")
            status = data.get("status", Subscription.Status.ACTIVE)


        gym = self.context["request"].parser_context["kwargs"]["gym_id"]


        if status == Subscription.Status.ACTIVE:

            existing_subscription = Subscription.objects.filter(
                gym_id=gym,
                member=member,
                status=Subscription.Status.ACTIVE,
            )

            # 5. If updating, exclude the subscription we're currently editing.
            if self.instance:
                existing_subscription = existing_subscription.exclude(
                    pk=self.instance.pk
                )

            # 6. Reject if another active subscription exists.
            if existing_subscription.exists():
                raise serializers.ValidationError(
                    "This member already has an active subscription."
                )

        return data
