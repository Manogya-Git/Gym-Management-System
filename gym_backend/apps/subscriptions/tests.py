from datetime import date, timedelta

from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.gyms.models import Gym, GymStaff
from apps.members.models import Member
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription


class SubscriptionAPITests(APITestCase):

    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpassword123",
        )

        # Create gym
        self.gym = Gym.objects.create(
            name="Test Gym",
            owner=self.user,
        )

        self.gym_staff = GymStaff.objects.create(
            user=self.user,
            gym=self.gym,
            role=GymStaff.Role.OWNER,
            is_active=True,
        )

        # Create member
        self.member = Member.objects.create(
            gym=self.gym,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="9800000000",
            date_of_birth=date(2000, 1, 1),
        )

        # Create plan
        self.plan = Plan.objects.create(
            gym=self.gym,
            name=Plan.Name.MONTHLY,
            price=2000,
            duration_days=30,
        )

        # Create an active subscription
        self.subscription = Subscription.objects.create(
            gym=self.gym,
            member=self.member,
            plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=Subscription.Status.ACTIVE,
        )

    def test_database_prevents_multiple_active_subscriptions_for_same_member(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Subscription.objects.create(
                    gym=self.gym,
                    member=self.member,
                    plan=self.plan,
                    start_date=self.subscription.start_date,
                    end_date=self.subscription.end_date,
                    status=Subscription.Status.ACTIVE,
                )

    def test_cannot_create_duplicate_active_subscription(self):
        # Authenticate as the gym owner
        self.client.force_authenticate(user=self.user)

        # Send a POST request to create another active subscription
        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/subscriptions/",
            {
                "member": self.member.id,
                "plan": self.plan.id,
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=30)),
                "status": Subscription.Status.ACTIVE,
            },
            format="json",
        )

        # The serializer should reject the duplicate
        self.assertEqual(response.status_code, 400)

        # Check that no second active subscription was created
        active_subscriptions = Subscription.objects.filter(
            gym=self.gym,
            member=self.member,
            status=Subscription.Status.ACTIVE,
        ).count()

        self.assertEqual(active_subscriptions, 1)

    def test_owner_can_update_subscription_end_date(self):
        self.client.force_authenticate(user=self.user)

        new_end_date = date.today() + timedelta(days=60)

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/subscriptions/{self.subscription.id}/",
            {
                "end_date": str(new_end_date),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.subscription.refresh_from_db()

        self.assertEqual(self.subscription.end_date, new_end_date)

    def test_user_cannot_access_another_gyms_subscription(self):
    # Create another user
        second_user = User.objects.create_user(
            email="secondowner@example.com",
            password="testpassword123",
        )

        # Create another gym
        second_gym = Gym.objects.create(
            name="Second Gym",
            owner=second_user,
        )

        # Make the second user staff of the second gym
        GymStaff.objects.create(
            user=second_user,
            gym=second_gym,
            role=GymStaff.Role.OWNER,
            is_active=True,
        )

        # Authenticate as the second gym's owner
        self.client.force_authenticate(user=second_user)

        # Try to access the first gym's subscription
        response = self.client.get(
            f"/api/v1/gyms/{second_gym.id}/subscriptions/{self.subscription.id}/"
        )

        # The subscription should not be accessible
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_update_another_gyms_subscription(self):
        # Create another user
        second_user = User.objects.create_user(
            email="secondowner@example.com",
            password="testpassword123",
        )

        # Create another gym
        second_gym = Gym.objects.create(
            name="Second Gym",
            owner=second_user,
        )

        # Make the second user staff of the second gym
        GymStaff.objects.create(
            user=second_user,
            gym=second_gym,
            role=GymStaff.Role.OWNER,
            is_active=True,
        )

        # Authenticate as the second gym's owner
        self.client.force_authenticate(user=second_user)

        # Try to update the first gym's subscription
        response = self.client.patch(
            f"/api/v1/gyms/{second_gym.id}/subscriptions/{self.subscription.id}/",
            {
                "end_date": str(date.today() + timedelta(days=60)),
            },
            format="json",
        )

        # The subscription should not be accessible
        self.assertEqual(response.status_code, 404)

        # Confirm the original subscription was not changed
        self.subscription.refresh_from_db()

        self.assertNotEqual(
            self.subscription.end_date,
            date.today() + timedelta(days=60),
        )
