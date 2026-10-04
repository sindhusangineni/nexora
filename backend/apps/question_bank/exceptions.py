from django.core.exceptions import ValidationError


class QuestionBankError(Exception):
    """Base exception for all Question Bank domain errors."""


class InvalidStatusTransitionError(QuestionBankError, ValidationError):
    """Raised when an illegal question version lifecycle transition is attempted."""


class ImmutableVersionError(QuestionBankError, ValidationError):
    """Raised when attempting to mutate content fields of an approved, published, or archived version."""


class PublicationValidationError(QuestionBankError, ValidationError):
    """Raised when a question version fails publication criteria."""


class ContentRepresentationError(QuestionBankError, ValidationError):
    """Raised when a question version does not have exactly one valid type-specific content representation."""


class InvalidTopicError(QuestionBankError, ValidationError):
    """Raised when one or more topic IDs associated with a question are invalid or not found."""


class PublicationConflictError(QuestionBankError):
    """Raised when a publication conflict occurs, such as a concurrent publication or an existing published version."""
    code = "PUBLICATION_CONFLICT"


class VersionCreationConflictError(QuestionBankError):
    """Raised when a concurrent conflict occurs while creating a new question version."""
    code = "VERSION_CREATION_CONFLICT"
