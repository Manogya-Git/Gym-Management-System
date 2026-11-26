from django.utils import timezone
from apps.subscriptions.models import Subscription
from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework.generics import ListCreateAPIView, get_object_or_404, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from apps.gyms.models import GymStaff

from .models import Payment
from .serializers import PaymentSerializer,PaymentStatusUpdateSerializer
from django.db import transaction

class PaymentListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_gym_staff(self):
        return get_object_or_404(
            GymStaff,
            gym_id=self.kwargs['gym_id'],
            user=self.request.user,
            is_active=True,
        )

    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        member_id = self.request.query_params.get("member")
        gym_payment = Payment.objects.filter(gym=gym_staff.gym)
        if member_id:
            gym_payment = gym_payment.filter(member_id=member_id)
        return gym_payment

    def perform_create(self, serializer):
        with transaction.atomic():
            validated_data = serializer.validated_data
            gym_staff = self.get_gym_staff()

            try:
                subscription = Subscription.objects.select_for_update().get(
                    id=validated_data["subscription"].id,
                    gym=gym_staff.gym
                )
            except Subscription.DoesNotExist:
                raise ValidationError(
                    "This subscription does not belong to your gym."
                )

            if subscription.member != validated_data["member"]:
                raise ValidationError(
                    "This subscription does not belong to this member."
                )

            if Payment.objects.filter(
                subscription=subscription,
                status=Payment.Status.COMPLETED
            ).exists():
                raise ValidationError(
                    "This subscription has already been paid."
                )

            if validated_data["payment_method"] != Payment.PaymentMethod.CASH:
                raise ValidationError("Only cash payments are allowed.")

            serializer.save(
                gym=gym_staff.gym,
                member=validated_data["member"],
                subscription=subscription,
                amount=subscription.plan.price,
                payment_method=validated_data["payment_method"],
                status=Payment.Status.COMPLETED,
                paid_at=timezone.now()
            )
            
class PaymentDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return PaymentStatusUpdateSerializer
        return PaymentSerializer
        

    def get_gym_staff(self):
        return get_object_or_404(
            GymStaff,
            gym_id=self.kwargs['gym_id'],
            user=self.request.user,
            is_active=True,
        )

    def get_queryset(self):
        gym_staff = self.get_gym_staff()
        return Payment.objects.filter(gym=gym_staff.gym)
