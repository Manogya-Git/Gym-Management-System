from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.gyms.models import Gym, GymStaff

User = get_user_model()


class GymsAndStaffAPITests(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            first_name="Gym",
            last_name="Owner",
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="StrongPassword123!",
            first_name="Front",
            last_name="Desk",
        )
        self.trainer_user = User.objects.create_user(
            email="trainer@example.com",
            password="StrongPassword123!",
            first_name="Head",
            last_name="Trainer",
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="StrongPassword123!",
        )

        self.gym = Gym.objects.create(name="Iron Core", owner=self.owner)
        self.owner_membership = GymStaff.objects.create(
            user=self.owner,
            gym=self.gym,
            role=GymStaff.Role.OWNER,
            is_active=True,
        )
        self.staff_membership = GymStaff.objects.create(
            user=self.staff_user,
            gym=self.gym,
            role=GymStaff.Role.STAFF,
            is_active=True,
        )

        self.other_gym = Gym.objects.create(name="Other Gym", owner=self.outsider)
        GymStaff.objects.create(
            user=self.outsider,
            gym=self.other_gym,
            role=GymStaff.Role.OWNER,
            is_active=True,
        )

    def test_authenticated_user_can_create_gym_and_becomes_owner(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(
            "/api/v1/gyms/",
            {
                "name": "Apex Fitness",
                "timezone": "Asia/Kathmandu",
                "currency": "NPR",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        gym = Gym.objects.get(id=response.data["id"])
        self.assertEqual(gym.owner, self.outsider)
        self.assertTrue(
            GymStaff.objects.filter(
                gym=gym,
                user=self.outsider,
                role=GymStaff.Role.OWNER,
                is_active=True,
            ).exists()
        )

    def test_user_lists_only_gyms_where_active_staff(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get("/api/v1/gyms/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.gym.id)

        self.staff_membership.is_active = False
        self.staff_membership.save(update_fields=["is_active"])

        response_after = self.client.get("/api/v1/gyms/")
        self.assertEqual(response_after.status_code, 200)
        self.assertEqual(len(response_after.data), 0)

    def test_staff_can_retrieve_gym_detail_but_cannot_update_gym(self):
        self.client.force_authenticate(user=self.staff_user)

        get_response = self.client.get(f"/api/v1/gyms/{self.gym.id}/")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["name"], "Iron Core")

        patch_response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/",
            {"name": "Hacked Gym"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 403)

    def test_owner_can_update_gym_details(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/",
            {
                "name": "Iron Core Pro",
                "status": Gym.Status.SUSPENDED,
                "currency": "USD",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.gym.refresh_from_db()
        self.assertEqual(self.gym.name, "Iron Core Pro")
        self.assertEqual(self.gym.status, Gym.Status.SUSPENDED)
        self.assertEqual(self.gym.currency, "USD")

    def test_non_member_cannot_retrieve_or_update_another_gym(self):
        self.client.force_authenticate(user=self.outsider)

        get_response = self.client.get(f"/api/v1/gyms/{self.gym.id}/")
        self.assertEqual(get_response.status_code, 404)

        patch_response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/",
            {"name": "Nope"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 404)

    def test_owner_can_add_staff_and_filter_by_role_and_active(self):
        self.client.force_authenticate(user=self.owner)

        create_response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/staff/",
            {
                "user": self.trainer_user.id,
                "role": GymStaff.Role.TRAINER,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["email"], "trainer@example.com")
        self.assertEqual(create_response.data["role"], GymStaff.Role.TRAINER)

        trainer_list = self.client.get(
            f"/api/v1/gyms/{self.gym.id}/staff/?role=TRAINER&is_active=true"
        )
        self.assertEqual(trainer_list.status_code, 200)
        self.assertEqual(len(trainer_list.data), 1)
        self.assertEqual(trainer_list.data[0]["user"], self.trainer_user.id)

    def test_duplicate_staff_assignment_returns_400(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/staff/",
            {
                "user": self.staff_user.id,
                "role": GymStaff.Role.TRAINER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_non_owner_staff_cannot_add_update_or_deactivate_staff(self):
        self.client.force_authenticate(user=self.staff_user)

        list_response = self.client.get(f"/api/v1/gyms/{self.gym.id}/staff/")
        self.assertEqual(list_response.status_code, 200)

        create_response = self.client.post(
            f"/api/v1/gyms/{self.gym.id}/staff/",
            {
                "user": self.trainer_user.id,
                "role": GymStaff.Role.TRAINER,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 403)

        patch_response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.staff_membership.id}/",
            {"role": GymStaff.Role.OWNER},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 403)

        delete_response = self.client.delete(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.owner_membership.id}/"
        )
        self.assertEqual(delete_response.status_code, 403)

    def test_non_member_cannot_access_gym_staff(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(f"/api/v1/gyms/{self.gym.id}/staff/")
        self.assertEqual(response.status_code, 404)

    def test_owner_can_update_staff_role_and_deactivate_staff(self):
        self.client.force_authenticate(user=self.owner)

        patch_response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.staff_membership.id}/",
            {"role": GymStaff.Role.TRAINER},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.staff_membership.refresh_from_db()
        self.assertEqual(self.staff_membership.role, GymStaff.Role.TRAINER)

        delete_response = self.client.delete(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.staff_membership.id}/"
        )
        self.assertEqual(delete_response.status_code, 204)
        self.staff_membership.refresh_from_db()
        self.assertFalse(self.staff_membership.is_active)

    def test_cannot_demote_or_deactivate_primary_gym_owner(self):
        self.client.force_authenticate(user=self.owner)

        demote_response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.owner_membership.id}/",
            {"role": GymStaff.Role.STAFF},
            format="json",
        )
        self.assertEqual(demote_response.status_code, 400)

        deactivate_response = self.client.patch(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.owner_membership.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(deactivate_response.status_code, 400)

        delete_response = self.client.delete(
            f"/api/v1/gyms/{self.gym.id}/staff/{self.owner_membership.id}/"
        )
        self.assertEqual(delete_response.status_code, 400)

        self.owner_membership.refresh_from_db()
        self.assertEqual(self.owner_membership.role, GymStaff.Role.OWNER)
        self.assertTrue(self.owner_membership.is_active)
