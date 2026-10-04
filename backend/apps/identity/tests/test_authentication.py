import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    user = User.objects.create_user(email="student@example.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.mark.django_db
class TestAuthentication:
    url = "/api/v1/auth/login/"

    def test_successful_login(self, api_client, student_user):
        payload = {
            "email": "Student@Example.com",
            "password": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Access token in body
        assert "access" in data
        assert len(data["access"]) > 20

        # Refresh token NOT in JSON response
        assert "refresh" not in data

        # User payload
        assert data["user"]["id"] == str(student_user.id)
        assert data["user"]["email"] == "student@example.com"
        assert data["user"]["email_verified"] is False
        assert data["user"]["roles"] == ["student"]

        # Refresh token in HttpOnly cookie
        assert "refresh_token" in response.cookies
        cookie = response.cookies["refresh_token"]
        assert cookie["httponly"] is True
        assert cookie.value != ""

    def test_login_invalid_password_returns_generic_error(self, api_client, student_user):
        payload = {
            "email": "student@example.com",
            "password": "WrongPassword999!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"
        assert data["error"]["message"] == "The email or password is incorrect."

    def test_login_nonexistent_email_returns_generic_error(self, api_client):
        payload = {
            "email": "nonexistent@example.com",
            "password": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"
        assert data["error"]["message"] == "The email or password is incorrect."

    def test_login_inactive_user_returns_generic_error(self, api_client):
        user = User.objects.create_user(email="inactive@example.com", password="StrongPassword123!")
        user.is_active = False
        user.save()

        payload = {
            "email": "inactive@example.com",
            "password": "StrongPassword123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"
        assert data["error"]["message"] == "The email or password is incorrect."

    def test_login_missing_fields_validation_error(self, api_client):
        response = api_client.post(self.url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "email" in data["error"]["fields"]
        assert "password" in data["error"]["fields"]
