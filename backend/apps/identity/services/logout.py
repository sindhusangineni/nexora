from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutService:
    def logout(self, refresh_token_str: str | None = None) -> None:
        if refresh_token_str:
            try:
                token = RefreshToken(refresh_token_str)
                # If SimpleJWT token blacklisting is available, blacklist the token
                if hasattr(token, "blacklist"):
                    token.blacklist()
            except (TokenError, Exception):
                # Even if token is already expired/invalid, logout still proceeds to clear client state
                pass
