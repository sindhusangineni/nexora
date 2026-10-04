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
def authenticated_client():
    user = User.objects.create_user(email="logout.user@example.com", password="StrongPassword123!")
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    client.cookies["refresh_token"] = str(refresh)
    return client


@pytest.mark.django_db
class TestLogout:
    url = "/api/v1/auth/logout/"

    def test_authenticated_logout_clears_cookie(self, authenticated_client):
        response = authenticated_client.post(self.url, {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Successfully logged out."

        # Verify cookie is cleared/expired
        cookie = response.cookies.get("refresh_token")
        assert cookie is not None
        # In Django, delete_cookie sets max_age=0 or expires in the past and value=''
        assert cookie.value == "" or cookie["max-age"] == 0

    def test_unauthenticated_logout_rejected(self, api_client):
        response = api_client.post(self.url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
