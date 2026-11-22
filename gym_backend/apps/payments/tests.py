from rest_framework.test import APITestCase
from django.urls import reverse
from apps.accounts.models import User
from apps.gyms.models import Gym, GymStaff
from apps.members.models import Member
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.payments.models import Payment

class PaymentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@test.com",
            password="testpassword123"
        )
        self.gym = Gym.objects.create(
            name="Test1 Gym",
            owner=self.user
        )
        self.gym_staff = GymStaff.objects.create(
            user=self.user,
            gym=self.gym,
            role=GymStaff.Role.OWNER
        )
        self.member = Member.objects.create(
            gym=self.gym,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            phone="9800000000",
            date_of_birth="2000-01-01"
        )
        self.plan = Plan.objects.create(
            gym=self.gym,
            name=Plan.Name.MONTHLY,
            description="Monthly membership",
            price=2000,
            duration_days=30
        )
        self.subscription = Subscription.objects.create(
            gym=self.gym,
            member=self.member,
            plan=self.plan,
            start_date="2026-11-22",
            end_date="2026-12-22",
            status=Subscription.Status.ACTIVE
        )
        self.payment = Payment.objects.create(
            gym=self.gym,
            member=self.member,
            subscription=self.subscription,
            amount=self.plan.price,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.COMPLETED
        )

    def test_owner_can_retrieve_own_gym_payment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/"
        )

        self.assertEqual(response.status_code, 200)
        