import uuid

from django.db import IntegrityError, transaction

from apps.question_bank.exceptions import (
    PublicationConflictError,
    QuestionBankError,
)
from apps.question_bank.models import (
    Question,
    QuestionStatus,
    QuestionVersion,
)
from apps.question_bank.services.lifecycle import transition_question_version_status


def _resolve_and_lock_version(
    version_or_id: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Resolve and row-lock a QuestionVersion within the current database transaction.
    Accepts QuestionVersion instance, Question instance (resolving to latest_version),
    or UUID / UUID string identifier.
    """
    if isinstance(version_or_id, Question):
        v = version_or_id.latest_version
        if not v:
            raise QuestionBankError(f"Question '{version_or_id.id}' has no versions.")
        pk = v.pk
    elif isinstance(version_or_id, QuestionVersion):
        pk = version_or_id.pk
    else:
        try:
            pk = uuid.UUID(str(version_or_id))
        except (ValueError, AttributeError, TypeError) as err:
            raise QuestionBankError(f"Invalid version identifier '{version_or_id}'.") from err

    try:
        return QuestionVersion.objects.select_for_update().get(pk=pk)
    except QuestionVersion.DoesNotExist:
        raise QuestionBankError(f"QuestionVersion '{pk}' does not exist.")


@transaction.atomic
def submit_question_version_for_review(
    version: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Use Case: Submit a DRAFT version for review.
    DRAFT -> REVIEW
    """
    locked_version = _resolve_and_lock_version(version)
    updated = transition_question_version_status(locked_version, QuestionStatus.REVIEW)
    if isinstance(version, QuestionVersion):
        version.status = updated.status
    return updated


@transaction.atomic
def approve_question_version(
    version: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Use Case: Approve a reviewed question version.
    REVIEW -> APPROVED
    """
    locked_version = _resolve_and_lock_version(version)
    updated = transition_question_version_status(locked_version, QuestionStatus.APPROVED)
    if isinstance(version, QuestionVersion):
        version.status = updated.status
    return updated


@transaction.atomic
def publish_question_version(
    version: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Use Case: Publish an approved question version.
    APPROVED -> PUBLISHED

    Orchestrates:
    1. Row-locking the version and parent Question to serialize publication attempts.
    2. Enforcing existing publication domain criteria and single content representation.
    3. Verifying that no other version of the Question is currently PUBLISHED.
    4. Translating concurrent unique constraint collisions to PublicationConflictError.
    """
    locked_version = _resolve_and_lock_version(version)

    # Lock parent question row to serialize concurrent publication attempts on the same Question
    Question.objects.select_for_update().get(pk=locked_version.question_id)

    # Application-level check for existing published version
    already_published = (
        QuestionVersion.objects.filter(
            question_id=locked_version.question_id,
            status=QuestionStatus.PUBLISHED,
        )
        .exclude(pk=locked_version.pk)
        .first()
    )
    if already_published:
        raise PublicationConflictError(
            f"Question {locked_version.question_id} already has a published version "
            f"(version {already_published.version_number}). "
            f"Only one version may be published per Question at a time."
        )

    try:
        updated_version = transition_question_version_status(
            locked_version, QuestionStatus.PUBLISHED
        )
    except IntegrityError as exc:
        if "unique_published_version_per_question" in str(exc):
            raise PublicationConflictError(
                f"Concurrent publication conflict: A version for Question "
                f"{locked_version.question_id} has already been published."
            ) from exc
        raise

    if isinstance(version, QuestionVersion):
        version.status = updated_version.status
    return updated_version


@transaction.atomic
def archive_question_version(
    version: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Use Case: Archive a published question version.
    PUBLISHED -> ARCHIVED
    """
    locked_version = _resolve_and_lock_version(version)
    updated = transition_question_version_status(locked_version, QuestionStatus.ARCHIVED)
    if isinstance(version, QuestionVersion):
        version.status = updated.status
    return updated


@transaction.atomic
def reject_question_version_to_draft(
    version: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Use Case: Send a version under review back to DRAFT for edits.
    REVIEW -> DRAFT
    """
    locked_version = _resolve_and_lock_version(version)
    updated = transition_question_version_status(locked_version, QuestionStatus.DRAFT)
    if isinstance(version, QuestionVersion):
        version.status = updated.status
    return updated


@transaction.atomic
def reopen_question_version_review(
    version: QuestionVersion | Question | uuid.UUID | str,
) -> QuestionVersion:
    """
    Use Case: Reopen review for an approved version prior to publication.
    APPROVED -> REVIEW
    """
    locked_version = _resolve_and_lock_version(version)
    updated = transition_question_version_status(locked_version, QuestionStatus.REVIEW)
    if isinstance(version, QuestionVersion):
        version.status = updated.status
    return updated


# Ergonomic operation aliases
submit_for_review = submit_question_version_for_review
approve_version = approve_question_version
publish_version = publish_question_version
archive_version = archive_question_version
reject_to_draft = reject_question_version_to_draft
send_back_to_draft = reject_question_version_to_draft
reopen_review = reopen_question_version_review
return_to_review = reopen_question_version_review
