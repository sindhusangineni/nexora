from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from django.db import models, transaction

from apps.attempts.authorization import (
    AuthorizationContext,
    validate_can_start_attempt,
)
from apps.attempts.exceptions import (
    InvalidDeliveryPayloadError,
    PaperNotEligibleError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptItem,
    AttemptItemChoice,
    AttemptResponse,
    AttemptStatus,
)
from apps.attempts.ports.assessment import (
    AssessmentPaperPort,
    DeliveryPayloadDTO,
)
from apps.attempts.services.advisory_lock import acquire_attempt_start_lock
from apps.attempts.services.timing import get_authoritative_now


def _validate_delivery_payload(payload: DeliveryPayloadDTO) -> None:
    """Validate assessment delivery payload to protect Attempts persistence invariants."""
    if not payload.is_eligible:
        raise PaperNotEligibleError(
            payload.eligibility_error
            or "Assessment paper is not eligible to be attempted."
        )

    if payload.duration_seconds <= 0:
        raise InvalidDeliveryPayloadError("Paper duration must be strictly positive.")

    if not payload.items:
        raise InvalidDeliveryPayloadError(
            "Paper delivery payload must contain at least one item."
        )

    paper_item_ids = [item.paper_item_id for item in payload.items]
    if len(paper_item_ids) != len(set(paper_item_ids)):
        raise InvalidDeliveryPayloadError(
            "Duplicate paper_item_id found in delivery payload."
        )

    orders = [item.presentation_order for item in payload.items]
    if len(orders) != len(set(orders)):
        raise InvalidDeliveryPayloadError(
            "Duplicate presentation_order found in delivery payload."
        )

    if any(order < 1 for order in orders):
        raise InvalidDeliveryPayloadError(
            "Item presentation_order must be greater than or equal to 1."
        )

    if any(item.allocated_marks <= Decimal("0") for item in payload.items):
        raise InvalidDeliveryPayloadError(
            "Item allocated_marks must be strictly positive."
        )

    if any(item.allocated_penalty < Decimal("0") for item in payload.items):
        raise InvalidDeliveryPayloadError(
            "Item allocated_penalty must be non-negative."
        )

    if any(not item.question_version_id for item in payload.items):
        raise InvalidDeliveryPayloadError(
            "Every paper item must have a valid question_version_id."
        )

    for item in payload.items:
        if item.choices:
            choice_positions = [c.presented_position for c in item.choices]
            if len(choice_positions) != len(set(choice_positions)):
                raise InvalidDeliveryPayloadError(
                    f"Duplicate choice presented_position in item {item.paper_item_id}."
                )
            if any(pos < 1 for pos in choice_positions):
                raise InvalidDeliveryPayloadError(
                    f"Choice presented_position must be >= 1 in item {item.paper_item_id}."
                )
            choice_ids = [c.choice_id for c in item.choices]
            if len(choice_ids) != len(set(choice_ids)):
                raise InvalidDeliveryPayloadError(
                    f"Duplicate choice_id in item {item.paper_item_id}."
                )

        if item.question_type == "MATCH_FOLLOWING" and item.match_pairs:
            left_ids = [m.left_item_id for m in item.match_pairs]
            right_ids = [m.right_item_id for m in item.match_pairs]
            if len(left_ids) != len(set(left_ids)):
                raise InvalidDeliveryPayloadError(
                    f"Duplicate left_item_id in match pairs for item {item.paper_item_id}."
                )
            if len(right_ids) != len(set(right_ids)):
                raise InvalidDeliveryPayloadError(
                    f"Duplicate right_item_id in match pairs for item {item.paper_item_id}."
                )


@transaction.atomic
def start_attempt(
    student_id: UUID,
    paper_id: UUID,
    authorization_context: AuthorizationContext,
    assessment_port: AssessmentPaperPort,
    now: datetime | None = None,
) -> Attempt:
    """
    Use Case: Start a new attempt or idempotently return an existing active attempt.

    Transaction & Concurrency Guarantees:
    1. Validates actor authorization before state mutation.
    2. Serializes concurrent requests for (student_id, paper_id) via PostgreSQL
       transaction-scoped advisory lock: pg_advisory_xact_lock(<64-bit-md5-key>).
    3. Idempotently returns existing IN_PROGRESS attempt if already present.
    4. Fetches and validates paper delivery snapshot via AssessmentPaperPort.
    5. Allocates next attempt_number safely.
    6. Materializes Attempt, AttemptItem snapshots, AttemptItemChoice snapshots,
       and initializes exactly one blank AttemptResponse (UNANSWERED) per item.
    7. Atomically commits and returns the Attempt instance.
    """
    validate_can_start_attempt(authorization_context, student_id)

    acquire_attempt_start_lock(student_id, paper_id)

    existing_attempt = (
        Attempt.objects.select_for_update()
        .filter(
            student_id=student_id,
            assessment_paper_id=paper_id,
            status=AttemptStatus.IN_PROGRESS,
        )
        .first()
    )
    if existing_attempt is not None:
        return existing_attempt

    payload = assessment_port.get_paper_delivery_payload(
        paper_id=paper_id,
        student_id=student_id,
    )
    _validate_delivery_payload(payload)

    max_attempt_number = (
        Attempt.objects.filter(
            student_id=student_id,
            assessment_paper_id=paper_id,
        ).aggregate(models.Max("attempt_number"))["attempt_number__max"]
    )
    next_attempt_number = (max_attempt_number or 0) + 1

    current_time = now if now is not None else get_authoritative_now()
    expires_at = current_time + timedelta(seconds=payload.duration_seconds)

    attempt = Attempt.objects.create(
        student_id=student_id,
        assessment_paper_id=paper_id,
        attempt_number=next_attempt_number,
        duration_seconds=payload.duration_seconds,
        started_at=current_time,
        expires_at=expires_at,
        status=AttemptStatus.IN_PROGRESS,
    )

    for item in payload.items:
        attempt_item = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=item.paper_item_id,
            question_id=item.question_id,
            question_version_id=item.question_version_id,
            assessment_section_id=item.assessment_section_id,
            presentation_order=item.presentation_order,
            allocated_marks=item.allocated_marks,
            allocated_penalty=item.allocated_penalty,
        )

        for choice in item.choices:
            AttemptItemChoice.objects.create(
                attempt_item=attempt_item,
                choice_id=choice.choice_id,
                presented_position=choice.presented_position,
            )

        AttemptResponse.objects.create(
            attempt_item=attempt_item,
            answer_state=AnswerState.UNANSWERED,
        )

    return attempt
