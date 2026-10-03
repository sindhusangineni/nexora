import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def active_user():
    return User.objects.create_user(email="user@example.com", password="StrongPassword123!")


@pytest.mark.django_db
class TestTokenRefresh:
    url = "/api/v1/auth/refresh/"

    def test_refresh_token_via_cookie(self, api_client, active_user):
        refresh = RefreshToken.for_user(active_user)
        api_client.cookies["refresh_token"] = str(refresh)

        response = api_client.post(self.url, {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert len(data["access"]) > 20

    def test_refresh_token_rejected_from_request_body_without_cookie(self, api_client, active_user):
        refresh = RefreshToken.for_user(active_user)
        payload = {"refresh": str(refresh)}

        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "refresh" in data["error"]["fields"]


    def test_refresh_with_invalid_token(self, api_client):
        api_client.cookies["refresh_token"] = "invalid.token.here"

        response = api_client.post(self.url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_refresh_with_missing_token(self, api_client):
        response = api_client.post(self.url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "refresh" in data["error"]["fields"]
