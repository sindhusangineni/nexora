from datetime import datetime
from uuid import UUID

from django.db import transaction

from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptExpired,
    AttemptNotFoundError,
    InvalidAttemptStateError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptItem,
    AttemptResponse,
    AttemptStatus,
)
from apps.attempts.ports.question_bank import QuestionBankPort
from apps.attempts.services.scoring import ScoringPolicy
from apps.attempts.services.submission import execute_timeout_submission
from apps.attempts.services.timing import get_authoritative_now, is_attempt_expired


def clear_response(
    *,
    attempt_id: UUID,
    attempt_item_id: UUID,
    authorization: AuthorizationContext,
    question_bank_port: QuestionBankPort | None = None,
    scoring_policy: ScoringPolicy | None = None,
    now: datetime | None = None,
) -> AttemptResponse:
    """
    Use Case: Reset a previously answered item back to UNANSWERED.

    Transaction & Concurrency Guarantees:
    1. Locks the Attempt row (select_for_update) inside an atomic transaction.
    2. Validates student ownership and IN_PROGRESS lifecycle state.
    3. If expired (now >= expires_at):
       - Preserves existing student answers without clearing.
       - Executes timeout auto-submission within the atomic block.
       - Commits transaction durably to PostgreSQL.
       - Raises AttemptExpired (HTTP 409) post-commit.
    4. If active (now < expires_at):
       - Resets AttemptResponse.answer_state = UNANSWERED.
       - Nullifies scalar fields and deletes child choice/match rows.
       - Preserves AttemptResponse row itself.
       - Commits transaction and returns the cleared AttemptResponse.
    """
    current_now = now if now is not None else get_authoritative_now()
    is_expired = False
    cleared_response: AttemptResponse | None = None

    with transaction.atomic():
        attempt = (
            Attempt.objects.select_for_update()
            .filter(id=attempt_id)
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        if not authorization.is_student or authorization.actor_id != attempt.student_id:
            raise AttemptAuthorizationError("Students may only mutate their own test attempts.")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStateError(
                f"Cannot clear response on attempt with status '{attempt.status}'."
            )

        attempt_item = (
            AttemptItem.objects.filter(id=attempt_item_id, attempt_id=attempt.id)
            .first()
        )
        if attempt_item is None:
            raise AttemptNotFoundError(
                f"AttemptItem '{attempt_item_id}' not found on attempt '{attempt_id}'."
            )

        if is_attempt_expired(attempt.expires_at, current_now):
            # Timed out! Preserve existing answers and commit timeout submission
            if scoring_policy is None:
                raise ValueError("A ScoringPolicy must be explicitly provided for timeout submission.")
            execute_timeout_submission(
                attempt=attempt,
                now=current_now,
                scoring_policy=scoring_policy,
                question_bank_port=question_bank_port,
            )
            is_expired = True
        else:
            resp = AttemptResponse.objects.select_for_update().get(attempt_item=attempt_item)
            resp.answer_state = AnswerState.UNANSWERED
            resp.boolean_response = None
            resp.assertion_reason_response = None
            resp.text_response = None
            resp.choices.all().delete()
            resp.matches.all().delete()
            resp.save()
            cleared_response = resp

    # Transaction committed durably before raising AttemptExpired
    if is_expired:
        raise AttemptExpired("Attempt has expired and has been submitted.")

    return cleared_response  # type: ignore[return-value]
