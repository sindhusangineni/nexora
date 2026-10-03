from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.permissions.roles import get_user_roles
from apps.identity.serializers.registration import UserRegistrationSerializer
from apps.identity.services.registration import RegistrationService


class RegistrationView(APIView):
    """
    Register a new user in the platform.
    Assigns the default Student role.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = RegistrationService().register_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response(
            {
                "message": "User registered successfully.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "email_verified": user.email_verified,
                    "roles": get_user_roles(user),
                },
            },
            status=status.HTTP_201_CREATED,
        )
