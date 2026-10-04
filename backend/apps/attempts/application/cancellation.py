from datetime import datetime
from uuid import UUID

from django.db import transaction

from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptNotFoundError,
    InvalidAttemptStateError,
)
from apps.attempts.models import Attempt, AttemptResult, AttemptStatus
from apps.attempts.models.enums import AttemptResultStatus
from apps.attempts.services.timing import get_authoritative_now


def cancel_attempt(
    *,
    attempt_id: UUID,
    reason: str,
    authorization: AuthorizationContext,
    now: datetime | None = None,
) -> tuple[Attempt, AttemptResult | None]:
    """
    Use Case: Cancel an attempt (either active IN_PROGRESS or submitted PENDING).

    Requirements:
    - Only authorized Superadmin.
    - Active attempt: IN_PROGRESS -> CANCELLED (preserve all historical data).
    - Submitted pending attempt: SUBMITTED -> CANCELLED, AttemptResult -> VOID.
    - Terminal attempts (EVALUATED, already CANCELLED, or FINAL result) cannot be cancelled.
    - Non-empty cancellation reason required.
    - Records cancelled_at, cancelled_by, cancellation_reason.
    """
    if not authorization.is_superadmin:
        raise AttemptAuthorizationError("Only authorized Superadmin may cancel attempts.")

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise InvalidAttemptStateError("A non-empty cancellation reason must be provided.")

    current_now = now if now is not None else get_authoritative_now()

    with transaction.atomic():
        attempt = (
            Attempt.objects.select_for_update()
            .filter(id=attempt_id)
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        if attempt.status == AttemptStatus.IN_PROGRESS:
            attempt.status = AttemptStatus.CANCELLED
            attempt.cancelled_at = current_now
            attempt.cancelled_by = authorization.actor_id
            attempt.cancellation_reason = clean_reason
            attempt.save()
            return attempt, None

        elif attempt.status == AttemptStatus.SUBMITTED:
            attempt_result = (
                AttemptResult.objects.select_for_update()
                .filter(attempt=attempt)
                .first()
            )
            if attempt_result is None or attempt_result.status != AttemptResultStatus.PENDING:
                raise InvalidAttemptStateError(
                    f"Cannot cancel submitted attempt with result status '{getattr(attempt_result, 'status', None)}'. Only PENDING results may be cancelled."
                )

            attempt.status = AttemptStatus.CANCELLED
            attempt.cancelled_at = current_now
            attempt.cancelled_by = authorization.actor_id
            attempt.cancellation_reason = clean_reason
            attempt.save()

            attempt_result.status = AttemptResultStatus.VOID
            attempt_result.finalized_at = None
            attempt_result.save()
            return attempt, attempt_result

        else:
            raise InvalidAttemptStateError(
                f"Cannot cancel attempt with status '{attempt.status}'. Only IN_PROGRESS or SUBMITTED (with PENDING result) attempts can be cancelled."
            )


def cancel_active_attempt(
    *,
    attempt_id: UUID,
    reason: str,
    authorization: AuthorizationContext,
    now: datetime | None = None,
) -> Attempt:
    """Convenience wrapper for cancelling an active (IN_PROGRESS) attempt."""
    attempt, _ = cancel_attempt(
        attempt_id=attempt_id,
        reason=reason,
        authorization=authorization,
        now=now,
    )
    return attempt


def cancel_submitted_attempt(
    *,
    attempt_id: UUID,
    reason: str,
    authorization: AuthorizationContext,
    now: datetime | None = None,
) -> tuple[Attempt, AttemptResult]:
    """Convenience wrapper for cancelling a submitted attempt with PENDING result."""
    attempt, result = cancel_attempt(
        attempt_id=attempt_id,
        reason=reason,
        authorization=authorization,
        now=now,
    )
    if result is None:
        raise InvalidAttemptStateError("Attempt did not have a result to cancel.")
    return attempt, result
