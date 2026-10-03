from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.serializers.token import TokenRefreshSerializer
from apps.identity.services.token import TokenService


class TokenRefreshView(APIView):
    """
    Refresh access token using the secure refresh cookie or payload token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        refresh_token_str = serializer.validated_data["refresh_token"]
        new_access_token = TokenService().refresh_access_token(refresh_token_str)

        return Response(
            {"access": new_access_token},
            status=status.HTTP_200_OK,
        )
