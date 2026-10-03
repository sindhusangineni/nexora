import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestRegistration:
    url = "/api/v1/auth/register/"

    def test_successful_registration(self, api_client):
        payload = {
            "email": "New.User@Example.Com",
            "password": "StrongPassword123!",
            "password_confirmation": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "User registered successfully."
        assert data["user"]["email"] == "new.user@example.com"
        assert data["user"]["email_verified"] is False
        assert "student" in data["user"]["roles"]
        assert "password" not in data["user"]
        assert "access" not in data  # No automatic login/token issuance

        # Verify user in database
        user = User.objects.get(email="new.user@example.com")
        assert user.check_password("StrongPassword123!")
        assert user.groups.filter(name="Student").exists()

    def test_duplicate_email_rejected(self, api_client):
        User.objects.create_user(email="existing@example.com", password="StrongPassword123!")

        payload = {
            "email": "Existing@Example.com",
            "password": "StrongPassword123!",
            "password_confirmation": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "email" in data["error"]["fields"]

    def test_password_confirmation_mismatch(self, api_client):
        payload = {
            "email": "user@example.com",
            "password": "StrongPassword123!",
            "password_confirmation": "DifferentPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "password_confirmation" in data["error"]["fields"]

    def test_invalid_email_format(self, api_client):
        payload = {
            "email": "invalid-email-format",
            "password": "StrongPassword123!",
            "password_confirmation": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "email" in data["error"]["fields"]

    def test_weak_password_rejected(self, api_client):
        payload = {
            "email": "user@example.com",
            "password": "123",
            "password_confirmation": "123",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "password" in data["error"]["fields"]

    def test_registration_assigns_student_group(self, api_client):
        payload = {
            "email": "student@example.com",
            "password": "StrongPassword123!",
            "password_confirmation": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="student@example.com")
        student_group = Group.objects.get(name="Student")
        assert not user.is_staff
        assert not user.is_superuser

    def test_registration_ignores_privilege_escalation_fields(self, api_client):
        payload = {
            "email": "attacker@example.com",
            "password": "StrongPassword123!",
            "password_confirmation": "StrongPassword123!",
            "is_staff": True,
            "is_superuser": True,
            "roles": ["superadmin"],
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="attacker@example.com")
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.groups.filter(name="Student").exists()
        assert not user.groups.filter(name="Superadmin").exists()

