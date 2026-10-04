import importlib
import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestCorsConfiguration:
    def test_cors_installed_apps_and_middleware(self):
        """Verify corsheaders is in INSTALLED_APPS and CorsMiddleware is before CommonMiddleware."""
        assert "corsheaders" in settings.INSTALLED_APPS

        middleware = list(settings.MIDDLEWARE)
        assert "corsheaders.middleware.CorsMiddleware" in middleware
        assert "django.middleware.common.CommonMiddleware" in middleware

        cors_idx = middleware.index("corsheaders.middleware.CorsMiddleware")
        common_idx = middleware.index("django.middleware.common.CommonMiddleware")
        assert cors_idx < common_idx, "CorsMiddleware must be placed before CommonMiddleware."

    def test_cors_base_settings_contract(self):
        """Verify credentialed CORS is enabled and wildcard CORS is not permitted."""
        assert settings.CORS_ALLOW_CREDENTIALS is True
        assert getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False) is False

    def test_cors_preflight_allowed_origin(self, api_client):
        """Preflight OPTIONS request from http://localhost:5173 returns allowed CORS headers."""
        response = api_client.options(
            "/api/v1/auth/login/",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        assert response.get("Access-Control-Allow-Credentials") == "true"

    def test_cors_preflight_disallowed_origin(self, api_client):
        """Preflight OPTIONS request from unauthorized origin does not return CORS headers."""
        response = api_client.options(
            "/api/v1/auth/login/",
            HTTP_ORIGIN="http://malicious-site.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        assert "Access-Control-Allow-Origin" not in response

    def test_cors_actual_request_allowed_origin(self, api_client):
        """Actual request with Origin header receives CORS response headers."""
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": "nobody@example.com", "password": "WrongPassword123!"},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
        )

        # Even with failed credentials (401), CORS headers must be present for permitted origin
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        assert response.get("Access-Control-Allow-Credentials") == "true"

    def test_environment_settings_separation(self):
        """Verify development and production settings modules maintain safe, environment-aware CORS configurations."""
        dev_settings = importlib.import_module("config.settings.development")
        prod_settings = importlib.import_module("config.settings.production")

        # Development explicitly allows localhost:5173 with credentials
        assert "http://localhost:5173" in dev_settings.CORS_ALLOWED_ORIGINS
        assert dev_settings.CORS_ALLOW_CREDENTIALS is True
        assert getattr(dev_settings, "CORS_ALLOW_ALL_ORIGINS", False) is False

        # Production defaults to empty allowed origins and never wildcards
        assert prod_settings.CORS_ALLOWED_ORIGINS == []
        assert prod_settings.CORS_ALLOW_CREDENTIALS is True
        assert getattr(prod_settings, "CORS_ALLOW_ALL_ORIGINS", False) is False
