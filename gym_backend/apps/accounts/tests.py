from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AccountsAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="existing@example.com",
            password="StrongPassword123!",
            first_name="Existing",
            last_name="User",
        )

    def test_user_can_register_and_obtain_jwt_token(self):
        response = self.client.post(
            "/api/v1/accounts/register/",
            {
                "email": "NewUser@Example.com",
                "first_name": "New",
                "last_name": "Member",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "newuser@example.com")
        self.assertNotIn("password", response.data)

        token_response = self.client.post(
            "/api/token/",
            {
                "email": "newuser@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)
        self.assertIn("access", token_response.data)

    def test_duplicate_email_registration_fails_case_insensitively(self):
        response = self.client.post(
            "/api/v1/accounts/register/",
            {
                "email": "EXISTING@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_weak_password_registration_fails(self):
        response = self.client.post(
            "/api/v1/accounts/register/",
            {
                "email": "weak@example.com",
                "password": "123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_unauthenticated_user_cannot_access_me(self):
        response = self.client.get("/api/v1/accounts/me/")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_retrieve_and_update_me(self):
        self.client.force_authenticate(user=self.user)

        get_response = self.client.get("/api/v1/accounts/me/")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["email"], "existing@example.com")

        patch_response = self.client.patch(
            "/api/v1/accounts/me/",
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "changed@example.com",
            },
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "existing@example.com")
