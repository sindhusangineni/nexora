from apps.question_bank.exceptions import (
    ImmutableVersionError,
    InvalidStatusTransitionError,
)
from apps.question_bank.models.enums import QuestionStatus

VALID_TRANSITIONS: dict[str, set[str]] = {
    QuestionStatus.DRAFT: {QuestionStatus.REVIEW},
    QuestionStatus.REVIEW: {QuestionStatus.DRAFT, QuestionStatus.APPROVED},
    QuestionStatus.APPROVED: {QuestionStatus.REVIEW, QuestionStatus.PUBLISHED},
    QuestionStatus.PUBLISHED: {QuestionStatus.ARCHIVED},
    QuestionStatus.ARCHIVED: set(),  # terminal state
}

IMMUTABLE_STATUSES: set[str] = {
    QuestionStatus.APPROVED,
    QuestionStatus.PUBLISHED,
    QuestionStatus.ARCHIVED,
}

CONTENT_FIELDS: set[str] = {
    "text",
    "explanation",
    "question_type",
    "difficulty",
    "version_number",
    "question_id",
    "source_type",
    "source_name",
    "source_reference",
    "source_year",
    "external_question_id",
}


def validate_status_transition(old_status: str, new_status: str) -> None:
    """
    Validate that transitioning from old_status to new_status is permitted.
    Raises InvalidStatusTransitionError if illegal.
    """
    if old_status == new_status:
        return

    allowed = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(
            f"Invalid question version status transition from '{old_status}' to '{new_status}'. "
            f"Allowed transitions from '{old_status}': {sorted(list(allowed)) or 'None (terminal state)'}."
        )


def validate_version_immutability(old_version, new_version) -> None:
    """
    Ensure that approved, published, or archived versions cannot have their content mutated.
    Raises ImmutableVersionError if content modification is attempted.
    """
    if old_version.status in IMMUTABLE_STATUSES:
        for field_name in CONTENT_FIELDS:
            old_val = getattr(old_version, field_name)
            new_val = getattr(new_version, field_name)
            if old_val != new_val:
                raise ImmutableVersionError(
                    f"Cannot modify field '{field_name}' on a question version with status '{old_version.status}'. "
                    f"Versions with status in {sorted(list(IMMUTABLE_STATUSES))} are immutable. "
                    f"Create a new draft version to make changes."
                )
