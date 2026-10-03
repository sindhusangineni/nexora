from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.exceptions import InvalidCredentialsException

User = get_user_model()


class AuthenticationService:
    def authenticate_user(self, email: str, password: str) -> tuple[User, RefreshToken]:
        normalized_email = email.strip().lower()

        user = authenticate(username=normalized_email, password=password)
        if user is None:
            raise InvalidCredentialsException()

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh_token = RefreshToken.for_user(user)

        return user, refresh_token

