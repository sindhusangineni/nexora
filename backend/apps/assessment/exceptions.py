from rest_framework import status

from shared.api.errors import ApplicationAPIException


class AssessmentError(ApplicationAPIException):
    def __init__(
        self,
        message: str = "An assessment error occurred.",
        code: str = "ASSESSMENT_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(code=code, message=message, status_code=status_code)


class AssessmentNotFoundError(AssessmentError):
    def __init__(self, message: str = "Assessment not found."):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class SectionNotFoundError(AssessmentError):
    def __init__(self, message: str = "Assessment section not found."):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class SelectionRuleNotFoundError(AssessmentError):
    def __init__(self, message: str = "Selection rule not found."):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PaperNotFoundError(AssessmentError):
    def __init__(self, message: str = "Assessment paper not found."):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AssessmentValidationError(AssessmentError):
    def __init__(self, message: str = "Assessment validation failed."):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidStatusTransitionError(AssessmentError):
    def __init__(self, message: str = "Invalid assessment status transition."):
        super().__init__(
            message=message,
            code="INVALID_STATUS_TRANSITION",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AssessmentImmutableError(AssessmentError):
    def __init__(self, message: str = "Assessment cannot be modified in its current status."):
        super().__init__(
            message=message,
            code="IMMUTABLE_ASSESSMENT",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AssessmentPaperImmutableError(AssessmentError):
    def __init__(self, message: str = "Assessment papers and items are immutable once generated."):
        super().__init__(
            message=message,
            code="IMMUTABLE_PAPER",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AssessmentNotPublishedError(AssessmentError):
    def __init__(self, message: str = "Cannot generate paper: assessment is not published."):
        super().__init__(
            message=message,
            code="ASSESSMENT_NOT_PUBLISHED",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AssessmentEmptyError(AssessmentError):
    def __init__(self, message: str = "Assessment has no selection rules configured."):
        super().__init__(
            message=message,
            code="ASSESSMENT_EMPTY",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InsufficientQuestionsError(AssessmentError):
    def __init__(self, message: str = "Insufficient eligible questions for selection rule."):
        super().__init__(
            message=message,
            code="INSUFFICIENT_QUESTIONS",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
