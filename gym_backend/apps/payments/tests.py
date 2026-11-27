from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.gyms.models import Gym, GymStaff
from apps.members.models import Member
from apps.payments.models import Payment
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription

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

        self.new_member = Member.objects.create(
            gym=self.gym,
            first_name="Sam",
            last_name="Doe",
            email="sam@test.com",
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
            status=Subscription.Status.ACTIVE,
            price=self.plan.price,
        )
        self.new_subscription = Subscription.objects.create(
            gym=self.gym,
            member=self.new_member,
            plan=self.plan,
            start_date="2026-11-22",
            end_date="2026-12-22",
            status=Subscription.Status.ACTIVE,
            price=self.plan.price,
        )

        self.payment = Payment.objects.create(
            gym=self.gym,
            member=self.member,
            subscription=self.subscription,
            amount=self.plan.price,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.COMPLETED
        )
        self.second_user = User.objects.create_user(
            email="secondowner@test.com",
            password="testpassword123"
        )

        self.second_gym = Gym.objects.create(
            name="Second Test Gym",
            owner=self.second_user
        )

        GymStaff.objects.create(
            user=self.second_user,
            gym=self.second_gym,
            role=GymStaff.Role.OWNER
        )

        self.second_member = Member.objects.create(
            gym=self.second_gym,
            first_name="Jane",
            last_name="Doe",
            email="jane@test.com",
            phone="9800000001",
            date_of_birth="2001-01-01"
        )

        self.second_plan = Plan.objects.create(
            gym=self.second_gym,
            name=Plan.Name.MONTHLY,
            description="Second gym monthly membership",
            price=2500,
            duration_days=30
        )

        self.second_subscription = Subscription.objects.create(
            gym=self.second_gym,
            member=self.second_member,
            plan=self.second_plan,
            start_date="2026-11-22",
            end_date="2026-12-22",
            status=Subscription.Status.ACTIVE,
            price=self.second_plan.price,
        )

        self.second_payment = Payment.objects.create(
            gym=self.second_gym,
            member=self.second_member,
            subscription=self.second_subscription,
            amount=self.second_plan.price,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.COMPLETED
        )

    def test_owner_can_retrieve_own_gym_payment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/"
        )

        self.assertEqual(response.status_code, 200)

    def test_owner_cannot_retrieve_payment_from_another_gym_url(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/v1/gyms/{self.second_gym.id}/payments/{self.second_payment.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_refund_completed_payment(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
             {"status": Payment.Status.REFUNDED}
        )
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)

    def test_owner_cannot_reactivate_refunded_payment(self):
        self.client.force_authenticate(user=self.user)
        self.payment.status = Payment.Status.REFUNDED
        self.payment.save()
        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
            {"status": Payment.Status.COMPLETED},
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)

    def test_owner_can_create_cash_payment(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "member": self.new_member.id,
            "subscription": self.new_subscription.id,
            "payment_method": Payment.PaymentMethod.CASH
        }
        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            data,
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount"], "2000.00")
        self.assertEqual(response.data["status"], Payment.Status.COMPLETED)
        self.assertEqual(
            Payment.objects.filter(subscription=self.new_subscription).count(),
            1
        )
        

    def test_owner_cannot_create_duplicate_payment(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "member": self.member.id,
            "subscription": self.subscription.id,
            "payment_method": Payment.PaymentMethod.CASH
        }
        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            data,
            format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            Payment.objects.filter(subscription=self.subscription).count(),
            1
        )

    def test_owner_cannot_create_payment_for_another_gym(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "member": self.second_member.id,
            "subscription": self.second_subscription.id,
            "payment_method": Payment.PaymentMethod.CASH
        }
        response = self.client.post(
                    f"/api/v1/gyms/{self.gym.id}/payments/",
                    data,
                    format="json"
                )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
                    Payment.objects.filter(subscription=self.second_subscription).count(),
                    1
                )

    def test_owner_cannot_create_payment_for_another_member_subscription(self):
        self.client.force_authenticate(user=self.user)
        data = {
                    "member": self.member.id,
                    "subscription": self.new_subscription.id,
                    "payment_method": Payment.PaymentMethod.CASH
                }
        response = self.client.post(
                    f"/api/v1/gyms/{self.gym.id}/payments/",
                    data,
                    format="json"
                )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
                    Payment.objects.filter(subscription=self.new_subscription).count(),
                    0
                )

    def test_owner_cannot_create_non_cash_payment(self):
        self.client.force_authenticate(user=self.user)

        data = {
            "member": self.new_member.id,
            "subscription": self.new_subscription.id,
            "payment_method": Payment.PaymentMethod.ESEWA
        }

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            Payment.objects.filter(subscription=self.new_subscription).count(),
            0
        )

    def test_owner_can_complete_pending_payment(self):
        self.client.force_authenticate(user=self.user)
        self.payment.status = Payment.Status.PENDING
        self.payment.save()

        data = {
            "status": Payment.Status.COMPLETED
        }
        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
            data,
            format="json"
        )
        self.assertEqual(response.status_code, 200)

        self.payment.refresh_from_db()

        self.assertEqual(self.payment.status, Payment.Status.COMPLETED)

    def test_owner_cannot_update_another_gyms_payment(self):
        self.client.force_authenticate(user=self.user)

        data = {
            "status": Payment.Status.REFUNDED
        }

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.second_payment.id}/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 404)

        self.second_payment.refresh_from_db()

        self.assertEqual(
            self.second_payment.status,
            Payment.Status.COMPLETED
        )

    def test_owner_cannot_update_failed_payment(self):
        self.client.force_authenticate(user=self.user)

        self.payment.status = Payment.Status.FAILED
        self.payment.save()

        data = {
            "status": Payment.Status.COMPLETED
        }

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED
        )

    def test_unauthenticated_user_cannot_create_payment(self):
        data = {
            "member": self.new_member.id,
            "subscription": self.new_subscription.id,
            "payment_method": Payment.PaymentMethod.CASH
        }

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            Payment.objects.filter(subscription=self.new_subscription).count(),
            0
        )

    def test_owner_can_list_own_gym_payments(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["gym"],
            self.gym.id
        )

    def test_owner_can_filter_payments_by_member(self):
        self.client.force_authenticate(user=self.user)

        # Create another payment for a different member in the same gym
        Payment.objects.create(
            gym=self.gym,
            member=self.new_member,
            subscription=self.new_subscription,
            amount=self.plan.price,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.COMPLETED,
        )

        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/?member={self.member.id}"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["member"],
            self.member.id
        )

    def test_owner_cannot_access_another_gyms_payments_using_member_filter(self):
        # Authenticate as the owner of Gym 1
        self.client.force_authenticate(user=self.user)

        # Request Gym 1 payments using a member ID from Gym 2
        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/?member={self.second_member.id}"
        )

        # The request should succeed, but return no payments
        self.assertEqual(response.status_code, 200)

        # Gym 2's payment must not appear in Gym 1's results
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_user_cannot_list_payments(self):
        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/"
        )

        self.assertEqual(response.status_code, 401)

    def test_non_member_cannot_list_another_gyms_payments(self):
        self.client.force_authenticate(user=self.second_user)

        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/"
        )

        self.assertEqual(response.status_code, 404)

    def test_non_member_cannot_create_payment_in_another_gym(self):
        self.client.force_authenticate(user=self.second_user)

        data = {
            "member": self.new_member.id,
            "subscription": self.new_subscription.id,
            "payment_method": Payment.PaymentMethod.CASH
        }

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            Payment.objects.filter(
                subscription=self.new_subscription
            ).count(),
            0
        )

    def test_owner_cannot_retrieve_another_gyms_payment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.second_payment.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_cannot_refund_already_refunded_payment(self):
        self.client.force_authenticate(user=self.user)

        self.payment.status = Payment.Status.REFUNDED
        self.payment.save()

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
            {"status": Payment.Status.REFUNDED},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.REFUNDED
        )

    def test_database_prevents_duplicate_completed_payment(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    gym=self.gym,
                    member=self.member,
                    subscription=self.subscription,
                    amount=self.plan.price,
                    payment_method=Payment.PaymentMethod.CASH,
                    status=Payment.Status.COMPLETED,
                )

    def test_cash_payment_reactivates_expired_subscription(self):
        self.client.force_authenticate(user=self.user)
        today = timezone.localdate()
        self.new_subscription.start_date = today - timedelta(days=40)
        self.new_subscription.end_date = today - timedelta(days=10)
        self.new_subscription.status = Subscription.Status.EXPIRED
        self.new_subscription.save()

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            {
                "member": self.new_member.id,
                "subscription": self.new_subscription.id,
                "payment_method": Payment.PaymentMethod.CASH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data["paid_at"])
        self.new_subscription.refresh_from_db()
        self.assertEqual(self.new_subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(self.new_subscription.start_date, today)
        self.assertEqual(
            self.new_subscription.end_date,
            today + timedelta(days=self.plan.duration_days),
        )

    def test_completing_pending_payment_reactivates_cancelled_subscription(self):
        self.client.force_authenticate(user=self.user)
        today = timezone.localdate()
        self.new_subscription.start_date = today - timedelta(days=15)
        self.new_subscription.end_date = today + timedelta(days=15)
        self.new_subscription.status = Subscription.Status.CANCELLED
        self.new_subscription.save()

        quarterly_plan = Plan.objects.create(
            gym=self.gym,
            name=Plan.Name.QUARTERLY,
            description="Quarterly membership",
            price=5500,
            duration_days=90,
        )
        pending_payment = Payment.objects.create(
            gym=self.gym,
            member=self.new_member,
            subscription=self.new_subscription,
            plan=quarterly_plan,
            amount=quarterly_plan.price,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.PENDING,
        )

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{pending_payment.id}/",
            {"status": Payment.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        pending_payment.refresh_from_db()
        self.assertIsNotNone(pending_payment.paid_at)
        self.new_subscription.refresh_from_db()
        self.assertEqual(self.new_subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(self.new_subscription.plan, quarterly_plan)
        self.assertEqual(self.new_subscription.price, quarterly_plan.price)
        self.assertEqual(self.new_subscription.start_date, today)
        self.assertEqual(
            self.new_subscription.end_date,
            today + timedelta(days=quarterly_plan.duration_days),
        )

    def test_cash_payment_with_new_plan_extends_active_subscription(self):
        self.client.force_authenticate(user=self.user)
        today = timezone.localdate()
        self.new_subscription.start_date = today
        self.new_subscription.end_date = today + timedelta(days=30)
        self.new_subscription.status = Subscription.Status.ACTIVE
        self.new_subscription.save()
        original_end_date = self.new_subscription.end_date

        yearly_plan = Plan.objects.create(
            gym=self.gym,
            name=Plan.Name.YEARLY,
            description="Yearly membership",
            price=18000,
            duration_days=365,
        )

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            {
                "member": self.new_member.id,
                "subscription": self.new_subscription.id,
                "plan": yearly_plan.id,
                "payment_method": Payment.PaymentMethod.CASH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount"], "18000.00")
        self.new_subscription.refresh_from_db()
        self.assertEqual(self.new_subscription.plan, yearly_plan)
        self.assertEqual(self.new_subscription.price, yearly_plan.price)
        self.assertEqual(
            self.new_subscription.end_date,
            original_end_date + timedelta(days=yearly_plan.duration_days),
        )

    def test_refunding_completed_payment_cancels_active_subscription(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
            {"status": Payment.Status.REFUNDED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.subscription.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.subscription.status, Subscription.Status.CANCELLED)

    def test_reactivating_payment_fails_when_member_has_other_active_subscription(self):
        self.client.force_authenticate(user=self.user)
        today = timezone.localdate()
        expired_sub = Subscription.objects.create(
            gym=self.gym,
            member=self.member,
            plan=self.plan,
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=30),
            status=Subscription.Status.EXPIRED,
            price=self.plan.price,
        )

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/payments/",
            {
                "member": self.member.id,
                "subscription": expired_sub.id,
                "payment_method": Payment.PaymentMethod.CASH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.filter(subscription=expired_sub).count(), 0)
        expired_sub.refresh_from_db()
        self.assertEqual(expired_sub.status, Subscription.Status.EXPIRED)

    def test_cancelling_pending_payment_does_not_modify_subscription(self):
        self.client.force_authenticate(user=self.user)
        pending_payment = Payment.objects.create(
            gym=self.gym,
            member=self.new_member,
            subscription=self.new_subscription,
            plan=self.plan,
            amount=self.plan.price,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.PENDING,
        )

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{pending_payment.id}/",
            {"status": Payment.Status.CANCELLED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        pending_payment.refresh_from_db()
        self.new_subscription.refresh_from_db()
        self.assertEqual(pending_payment.status, Payment.Status.CANCELLED)
        self.assertIsNone(pending_payment.paid_at)
        self.assertEqual(self.new_subscription.status, Subscription.Status.ACTIVE)
