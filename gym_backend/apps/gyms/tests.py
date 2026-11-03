from django.test import TestCase

from apps.accounts.models import User

from .models import Gym


class GymSlugTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create(
            email="owner@example.com",
            first_name="Gym",
            last_name="Owner",
        )

    def test_slug_is_generated_from_name(self):
        gym = Gym.objects.create(name="Round House Gym", owner=self.owner)

        self.assertEqual(gym.slug, "round-house-gym")

    def test_duplicate_names_get_unique_slugs(self):
        first_gym = Gym.objects.create(name="Round House Gym", owner=self.owner)
        second_gym = Gym.objects.create(name="Round House Gym", owner=self.owner)

        self.assertEqual(first_gym.slug, "round-house-gym")
        self.assertEqual(second_gym.slug, "round-house-gym-2")
