from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.db import transaction

from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptNotFoundError,
    InvalidAttemptStateError,
    InvalidEvaluationError,
)
from apps.attempts.models import (
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptResult,
    AttemptStatus,
    EvaluationState,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.attempts.ports.question_bank import QuestionBankPort
from apps.attempts.services.scoring import ScoringPolicy, get_scoring_policy
from apps.attempts.services.submission import recalculate_attempt_result
from apps.attempts.services.timing import get_authoritative_now


def evaluate_descriptive_item(
    *,
    attempt_id: UUID,
    attempt_item_id: UUID,
    evaluation_state: str,
    authorization: AuthorizationContext,
    marks_awarded: Decimal | None = None,
    marks_deducted: Decimal | None = None,
    evaluation_comments: str | None = None,
    scoring_policy: ScoringPolicy | None = None,
    question_bank_port: QuestionBankPort | None = None,
    now: datetime | None = None,
) -> tuple[Attempt, AttemptItem, AttemptEvaluation, AttemptResult]:
    """
    Use Case: Manually evaluate a descriptive question on a submitted attempt.

    Requirements:
    - Only authorized Superadmin evaluator.
    - Only submitted attempts.
    - Only AttemptItems whose evaluation is PENDING_EVALUATION.
    - Only descriptive questions.
    - marks_awarded >= 0, marks_awarded <= allocated_marks, marks_deducted >= 0.
    - evaluator_id and evaluated_at recorded.
    - Support: CORRECT, INCORRECT, PARTIALLY_CORRECT.
    - PARTIALLY_CORRECT must award strictly between 0 and allocated marks.
    - Prevent evaluation of objective items.
    - Prevent evaluation of already evaluated items.
    - Prevent evaluation of cancelled/void attempts.

    After evaluation:
    1. Lock Attempt
    2. Lock AttemptResult
    3. Update AttemptEvaluation
    4. Recalculate aggregate score, section results, counters
    5. If 0 pending evaluations remain:
       - AttemptResult -> FINAL, finalized_at = now, Attempt -> EVALUATED
    6. Otherwise remain:
       - Attempt -> SUBMITTED, AttemptResult -> PENDING
    """
    if not authorization.is_superadmin:
        raise AttemptAuthorizationError("Only authorized Superadmin may evaluate descriptive items.")

    current_now = now if now is not None else get_authoritative_now()

    with transaction.atomic():
        attempt = (
            Attempt.objects.select_for_update()
            .filter(id=attempt_id)
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        if attempt.status != AttemptStatus.SUBMITTED:
            raise InvalidAttemptStateError(
                f"Cannot evaluate attempt with status '{attempt.status}'. Only SUBMITTED attempts can be evaluated."
            )

        attempt_result = (
            AttemptResult.objects.select_for_update()
            .filter(attempt=attempt)
            .first()
        )
        if attempt_result is None or attempt_result.status != AttemptResultStatus.PENDING:
            raise InvalidAttemptStateError(
                f"Cannot evaluate attempt without a PENDING result (current status: {getattr(attempt_result, 'status', None)})."
            )

        attempt_item = (
            AttemptItem.objects.filter(id=attempt_item_id, attempt=attempt)
            .first()
        )
        if attempt_item is None:
            raise AttemptNotFoundError(
                f"AttemptItem '{attempt_item_id}' not found on attempt '{attempt_id}'."
            )

        if question_bank_port is None:
            from apps.attempts.adapters.question_bank import DatabaseQuestionBankAnswerKeyAdapter
            question_bank_port = DatabaseQuestionBankAnswerKeyAdapter()

        answer_keys = question_bank_port.get_objective_answer_keys([attempt_item.question_version_id])
        ak = answer_keys.get(attempt_item.question_version_id)
        if ak is None or ak.question_type != "DESCRIPTIVE":
            raise InvalidEvaluationError("Only descriptive items can be manually evaluated.")

        evaluation = (
            AttemptEvaluation.objects.select_for_update()
            .filter(attempt_item=attempt_item)
            .first()
        )
        if evaluation is None:
            raise InvalidEvaluationError("Evaluation record does not exist for this item.")

        if evaluation.evaluation_state != EvaluationState.PENDING_EVALUATION:
            raise InvalidEvaluationError(
                f"Item is not pending evaluation (current state: '{evaluation.evaluation_state}')."
            )

        # Marks validation
        allocated_marks = attempt_item.allocated_marks
        deducted = Decimal(str(marks_deducted)) if marks_deducted is not None else Decimal("0.0000")
        if deducted < Decimal("0.0000"):
            raise InvalidEvaluationError("marks_deducted cannot be negative.")

        if evaluation_state not in (
            EvaluationState.CORRECT,
            EvaluationState.INCORRECT,
            EvaluationState.PARTIALLY_CORRECT,
        ):
            raise InvalidEvaluationError(
                f"Invalid evaluation_state '{evaluation_state}'. Must be CORRECT, INCORRECT, or PARTIALLY_CORRECT."
            )

        if evaluation_state == EvaluationState.CORRECT:
            if marks_awarded is None:
                awarded = allocated_marks
            else:
                awarded = Decimal(str(marks_awarded))
                if awarded != allocated_marks:
                    raise InvalidEvaluationError("CORRECT evaluation must award full allocated marks.")
        elif evaluation_state == EvaluationState.INCORRECT:
            if marks_awarded is None:
                awarded = Decimal("0.0000")
            else:
                awarded = Decimal(str(marks_awarded))
                if awarded != Decimal("0.0000"):
                    raise InvalidEvaluationError("INCORRECT evaluation cannot award marks.")
        elif evaluation_state == EvaluationState.PARTIALLY_CORRECT:
            if marks_awarded is None:
                raise InvalidEvaluationError("marks_awarded is required for PARTIALLY_CORRECT.")
            awarded = Decimal(str(marks_awarded))
            if not (Decimal("0.0000") < awarded < allocated_marks):
                raise InvalidEvaluationError(
                    f"PARTIALLY_CORRECT must award strictly between 0 and allocated marks ({allocated_marks})."
                )

        if awarded < Decimal("0.0000"):
            raise InvalidEvaluationError("marks_awarded cannot be negative.")
        if awarded > allocated_marks:
            raise InvalidEvaluationError(f"marks_awarded cannot exceed allocated marks ({allocated_marks}).")

        # Update evaluation record
        evaluation.evaluation_state = evaluation_state
        evaluation.marks_awarded = awarded
        evaluation.marks_deducted = deducted
        evaluation.evaluator_id = authorization.actor_id
        evaluation.evaluated_at = current_now
        evaluation.evaluation_comments = evaluation_comments
        evaluation.save()

        # Recalculate aggregate results
        if scoring_policy is None:
            scoring_policy = get_scoring_policy(attempt.score_floor_policy)

        attempt, attempt_result = recalculate_attempt_result(
            attempt=attempt,
            scoring_policy=scoring_policy,
            now=current_now,
        )

        return attempt, attempt_item, evaluation, attempt_result
