from datetime import datetime
from uuid import UUID

from django.db import transaction

from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptNotFoundError,
    InvalidAttemptStateError,
)
from apps.attempts.models import (
    Attempt,
    AttemptResult,
    AttemptStatus,
    SubmissionReason,
)
from apps.attempts.ports.question_bank import QuestionBankPort
from apps.attempts.services.scoring import ScoringPolicy
from apps.attempts.services.submission import execute_submission
from apps.attempts.services.timing import get_authoritative_now, is_attempt_expired


def submit_attempt(
    *,
    attempt_id: UUID,
    authorization: AuthorizationContext,
    scoring_policy: ScoringPolicy | None = None,
    question_bank_port: QuestionBankPort | None = None,
    now: datetime | None = None,
) -> tuple[Attempt, AttemptResult]:
    """
    Use Case: Submit an active student attempt (MANUAL or TIMEOUT).
    """
    if question_bank_port is None:
        from apps.attempts.adapters.question_bank import DatabaseQuestionBankAnswerKeyAdapter
        question_bank_port = DatabaseQuestionBankAnswerKeyAdapter()

    current_now = now if now is not None else get_authoritative_now()

    with transaction.atomic():
        attempt = (
            Attempt.objects.select_for_update()
            .filter(id=attempt_id)
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        if scoring_policy is None:
            raise ValueError("A ScoringPolicy must be explicitly provided.")

        if not authorization.is_student or authorization.actor_id != attempt.student_id:
            raise AttemptAuthorizationError("Students may only submit their own test attempts.")

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStateError(
                f"Cannot submit attempt with status '{attempt.status}'."
            )

        if is_attempt_expired(attempt.expires_at, current_now):
            submission_reason = SubmissionReason.TIMEOUT
        else:
            submission_reason = SubmissionReason.MANUAL

        attempt, attempt_result = execute_submission(
            attempt=attempt,
            now=current_now,
            scoring_policy=scoring_policy,
            submission_reason=submission_reason,
            question_bank_port=question_bank_port,
        )

    return attempt, attempt_result
