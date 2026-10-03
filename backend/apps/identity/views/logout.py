from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.services.logout import LogoutService


class LogoutView(APIView):
    """
    Log out the current user session, revoke refresh token if available, and clear the refresh cookie.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "refresh_token")
        cookie_path = getattr(settings, "AUTH_COOKIE_PATH", "/api/v1/auth/")
        samesite = getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax")

        refresh_token = request.COOKIES.get(cookie_name) or request.data.get("refresh")
        LogoutService().logout(refresh_token_str=refresh_token)

        response = Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie(
            key=cookie_name,
            path=cookie_path,
            samesite=samesite,
        )

        return response
