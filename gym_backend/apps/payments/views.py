from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from apps.gyms.models import GymStaff

from .models import Payment
from .serializers import PaymentSerializer, PaymentStatusUpdateSerializer
from .services import create_payment, update_payment_status

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
        gym_staff = self.get_gym_staff()
        validated_data = serializer.validated_data
        payment = create_payment(
            gym=gym_staff.gym,
            member=validated_data["member"],
            subscription=validated_data["subscription"],
            plan=validated_data.get("plan"),
            payment_method=validated_data["payment_method"],
        )
        serializer.instance = payment
            
class PaymentDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
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

    def perform_update(self, serializer):
        payment = update_payment_status(
            payment=serializer.instance,
            new_status=serializer.validated_data["status"],
        )
        serializer.instance = payment
