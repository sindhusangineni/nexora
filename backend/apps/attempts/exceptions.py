from rest_framework import status
from shared.api.errors import ApplicationAPIException


class AttemptError(ApplicationAPIException):
    """Base exception for all Attempts domain and application errors."""

    def __init__(
        self,
        message: str = "An error occurred in the attempts domain.",
        code: str = "ATTEMPT_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(code=code, message=message, status_code=status_code)


class AttemptAuthorizationError(AttemptError):
    """Raised when an actor is not authorized to perform the requested attempt action."""

    def __init__(
        self,
        message: str = "Actor is not authorized to perform this attempt action.",
    ):
        super().__init__(
            code="AUTHORIZATION_FAILURE",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidAttemptStateError(AttemptError):
    """Raised when an action is attempted on an attempt with an incompatible status."""

    def __init__(
        self,
        message: str = "Attempt is not in the required state for this operation.",
    ):
        super().__init__(
            code="INVALID_ATTEMPT_STATE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AttemptExpired(AttemptError):
    """
    Raised when a mutation or query encounters an expired attempt.
    Maps to HTTP 409 Conflict per frozen v6 specification.
    """

    def __init__(
        self,
        message: str = "Attempt has expired and has been submitted.",
    ):
        super().__init__(
            code="ATTEMPT_EXPIRED",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class PaperNotEligibleError(AttemptError):
    """Raised when an assessment paper is not eligible to be attempted."""

    def __init__(
        self,
        message: str = "Assessment paper is not eligible to be attempted.",
    ):
        super().__init__(
            code="PAPER_NOT_ELIGIBLE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidDeliveryPayloadError(AttemptError):
    """Raised when an assessment delivery payload fails validation."""

    def __init__(
        self,
        message: str = "Assessment delivery payload fails validation.",
    ):
        super().__init__(
            code="INVALID_DELIVERY_PAYLOAD",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AttemptConflictError(AttemptError):
    """Raised when a concurrency or uniqueness conflict occurs."""

    def __init__(
        self,
        message: str = "A conflict occurred while creating or updating the attempt.",
    ):
        super().__init__(
            code="ATTEMPT_CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class AttemptNotFoundError(AttemptError):
    """Raised when an attempt cannot be found."""

    def __init__(
        self,
        message: str = "Attempt was not found.",
    ):
        super().__init__(
            code="ATTEMPT_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidResponseError(AttemptError):
    """Raised when a submitted response fails structural or domain validation."""

    def __init__(
        self,
        message: str = "Invalid response provided for this item.",
    ):
        super().__init__(
            code="INVALID_RESPONSE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidEvaluationError(AttemptError):
    """Raised when a descriptive item evaluation fails validation."""

    def __init__(
        self,
        message: str = "Invalid evaluation parameters.",
    ):
        super().__init__(
            code="INVALID_EVALUATION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

