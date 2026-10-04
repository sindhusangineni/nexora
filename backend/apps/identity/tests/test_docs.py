import pytest
from django.core.management import call_command
from django.test import override_settings
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def generated_schema():
    generator = SchemaGenerator()
    return generator.get_schema(request=None, public=True)


@pytest.mark.django_db
class TestOpenAPIDocumentation:
    def test_schema_endpoint_returns_successfully(self, api_client):
        response = api_client.get("/api/schema/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0

    def test_swagger_ui_returns_successfully(self, api_client):
        response = api_client.get("/api/docs/")
        assert response.status_code == status.HTTP_200_OK
        assert "swagger" in response.content.decode("utf-8").lower()

    def test_redoc_returns_successfully(self, api_client):
        response = api_client.get("/api/redoc/")
        assert response.status_code == status.HTTP_200_OK
        assert "redoc" in response.content.decode("utf-8").lower()

    def test_schema_generation_and_validation_succeeds(self):
        # Spectacular management command with validation and fail-on-warn
        call_command("spectacular", validate=True, fail_on_warn=True)

    def test_identity_endpoints_and_methods_present(self, generated_schema):
        paths = generated_schema["paths"]

        expected_endpoints = [
            "/api/v1/auth/register/",
            "/api/v1/auth/login/",
            "/api/v1/auth/refresh/",
            "/api/v1/auth/logout/",
        ]
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} missing from OpenAPI schema."
            assert "post" in paths[endpoint], f"POST method missing from {endpoint}."

    def test_authentication_tag_present(self, generated_schema):
        paths = generated_schema["paths"]
        expected_endpoints = [
            "/api/v1/auth/register/",
            "/api/v1/auth/login/",
            "/api/v1/auth/refresh/",
            "/api/v1/auth/logout/",
        ]
        for endpoint in expected_endpoints:
            tags = paths[endpoint]["post"].get("tags", [])
            assert "Authentication" in tags, f"'Authentication' tag missing from {endpoint}."

    def test_bearer_authentication_security_scheme_present(self, generated_schema):
        components = generated_schema["components"]
        assert "securitySchemes" in components
        security_schemes = components["securitySchemes"]
        assert "jwtAuth" in security_schemes

        jwt_scheme = security_schemes["jwtAuth"]
        assert jwt_scheme["type"] == "http"
        assert jwt_scheme["scheme"] == "bearer"
        assert jwt_scheme["bearerFormat"] == "JWT"

        # Logout must enforce jwtAuth
        logout_op = generated_schema["paths"]["/api/v1/auth/logout/"]["post"]
        assert "security" in logout_op
        assert any("jwtAuth" in s for s in logout_op["security"])

    def test_refresh_cookie_represented_appropriately(self, generated_schema):
        refresh_op = generated_schema["paths"]["/api/v1/auth/refresh/"]["post"]

        # Cookie parameter must be present and required
        parameters = refresh_op.get("parameters", [])
        cookie_param = next(
            (p for p in parameters if p.get("in") == "cookie" and p.get("name") == "refresh_token"),
            None,
        )
        assert cookie_param is not None, "refresh_token cookie parameter missing from /api/v1/auth/refresh/."
        assert cookie_param["required"] is True

        # Request body must not be required
        assert "requestBody" not in refresh_op

    def test_documented_response_schemas_present(self, generated_schema):
        schemas = generated_schema["components"]["schemas"]

        assert "RegistrationResponse" in schemas
        assert "LoginResponse" in schemas
        assert "TokenRefreshResponse" in schemas
        assert "MessageResponse" in schemas
        assert "UserResponse" in schemas

        # LoginResponse must only expose access token and user, never refresh token
        login_props = schemas["LoginResponse"]["properties"]
        assert "access" in login_props
        assert "user" in login_props
        assert "refresh" not in login_props
        assert "refresh_token" not in login_props

    def test_error_envelope_schema_present(self, generated_schema):
        schemas = generated_schema["components"]["schemas"]

        assert "ErrorResponse" in schemas
        assert "ErrorDetail" in schemas

        error_detail_props = schemas["ErrorDetail"]["properties"]
        assert "code" in error_detail_props
        assert "message" in error_detail_props
        assert "fields" in error_detail_props

        # fields must be optional
        assert "fields" not in schemas["ErrorDetail"].get("required", [])

    def test_documentation_disabled_when_enable_api_docs_false(self, api_client):
        with override_settings(ENABLE_API_DOCS=False):
            schema_resp = api_client.get("/api/schema/")
            assert schema_resp.status_code == status.HTTP_404_NOT_FOUND

            docs_resp = api_client.get("/api/docs/")
            assert docs_resp.status_code == status.HTTP_404_NOT_FOUND

            redoc_resp = api_client.get("/api/redoc/")
            assert redoc_resp.status_code == status.HTTP_404_NOT_FOUND
