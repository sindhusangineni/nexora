from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.permissions.roles import get_user_roles
from apps.identity.serializers.authentication import LoginSerializer
from apps.identity.serializers.errors import ErrorResponseSerializer
from apps.identity.serializers.responses import LoginResponseSerializer
from apps.identity.services.authentication import AuthenticationService


class LoginView(APIView):
    """
    Authenticate user credentials and issue an access token and secure refresh cookie.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Authenticate user and issue session tokens",
        description=(
            "Authenticates user credentials using email and password.\n\n"
            "- Returns a short-lived JWT access token in the response JSON.\n"
            "- Issues a longer-lived JWT refresh token stored in a secure HttpOnly cookie (`refresh_token`).\n"
            "- The refresh token is never exposed in the response JSON and cannot be accessed via JavaScript."
        ),
        request=LoginSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=LoginResponseSerializer,
                description=(
                    "Authentication successful. Returns access token in payload and sets "
                    "HttpOnly `refresh_token` cookie."
                ),
            ),
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, refresh_token = AuthenticationService().authenticate_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        response_data = {
            "access": str(refresh_token.access_token),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "email_verified": user.email_verified,
                "roles": get_user_roles(user),
            },
        }

        response = Response(response_data, status=status.HTTP_200_OK)

        response.set_cookie(
            key=getattr(settings, "AUTH_COOKIE_NAME", "refresh_token"),
            value=str(refresh_token),
            max_age=getattr(settings, "AUTH_COOKIE_MAX_AGE", 7 * 24 * 60 * 60),
            httponly=getattr(settings, "AUTH_COOKIE_HTTP_ONLY", True),
            secure=getattr(settings, "AUTH_COOKIE_SECURE", False),
            samesite=getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax"),
            path=getattr(settings, "AUTH_COOKIE_PATH", "/api/v1/auth/"),
        )

        return response
