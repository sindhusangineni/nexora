from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from apps.identity.exceptions import InvalidTokenException




class TokenService:
    def refresh_access_token(self, refresh_token_str: str) -> str:
        try:
            refresh = RefreshToken(refresh_token_str)
            return str(refresh.access_token)
        except TokenError:
            raise InvalidTokenException("Token is invalid or expired.")
