from rest_framework import status
from shared.api.errors import ApplicationAPIException


class IdentityAPIException(ApplicationAPIException):
    def __init__(
        self,
        code="ERROR",
        message="An error occurred.",
        status_code=status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(code=code, message=message, status_code=status_code)


class InvalidCredentialsException(IdentityAPIException):
    def __init__(self, message="The email or password is incorrect."):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InvalidTokenException(IdentityAPIException):
    def __init__(self, message="Token is invalid or expired."):
        super().__init__(
            code="INVALID_TOKEN",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
