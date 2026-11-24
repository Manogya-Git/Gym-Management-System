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
            status=Subscription.Status.ACTIVE
        )
        self.new_subscription = Subscription.objects.create(
            gym=self.gym,
            member=self.new_member,
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
            status=Subscription.Status.ACTIVE
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

    def test_owner_cannot_retrieve_another_gyms_payment(self):
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

    def test_owner_cannot_update_failed_payment(self):
        self.client.force_authenticate(user=self.user)

        self.payment.status = Payment.Status.FAILED
        self.payment.save()

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/payments/{self.payment.id}/",
            {"status": Payment.Status.COMPLETED},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED
        )


        








