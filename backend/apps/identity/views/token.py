from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.serializers.errors import ErrorResponseSerializer
from apps.identity.serializers.responses import TokenRefreshResponseSerializer
from apps.identity.serializers.token import TokenRefreshSerializer
from apps.identity.services.token import TokenService


class TokenRefreshView(APIView):
    """
    Refresh access token using the secure refresh cookie.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Refresh access token using secure cookie",
        description=(
            "Issues a new short-lived JWT access token using the longer-lived refresh token "
            "stored in the secure HttpOnly cookie (`refresh_token`).\n\n"
            "- The browser automatically transmits the HttpOnly cookie with the request.\n"
            "- The request body must remain empty; refresh tokens submitted in the body are rejected."
        ),
        request=None,
        parameters=[
            OpenApiParameter(
                name=getattr(settings, "AUTH_COOKIE_NAME", "refresh_token"),
                type=str,
                location=OpenApiParameter.COOKIE,
                required=True,
                description="HttpOnly cookie containing the longer-lived JWT refresh token.",
            ),
        ],
        responses={
            status.HTTP_200_OK: TokenRefreshResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        auth=[],
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        refresh_token_str = serializer.validated_data["refresh_token"]
        new_access_token = TokenService().refresh_access_token(refresh_token_str)

        return Response(
            {"access": new_access_token},
            status=status.HTTP_200_OK,
        )
