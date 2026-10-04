from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptResult,
    AttemptSectionResult,
    AttemptStatus,
    EvaluationState,
    SubmissionReason,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.attempts.ports.question_bank import QuestionBankPort
from apps.attempts.services.scoring import ScoringPolicy


def execute_submission(
    attempt: Attempt,
    now: datetime,
    scoring_policy: ScoringPolicy,
    submission_reason: str,
    question_bank_port: QuestionBankPort | None = None,
) -> tuple[Attempt, AttemptResult]:
    """
    Common submission workflow for both manual and timeout submissions.
    Executes within an existing database transaction:
    1. Sets attempt.submitted_at and attempt.submission_reason.
    2. Synchronously evaluates objective items against answer keys fetched via QuestionBankPort.
    3. Creates exactly one AttemptEvaluation per AttemptItem.
    4. Computes result counters and creates AttemptResult and AttemptSectionResults using
       the explicitly provided ScoringPolicy.
    5. Transitions Attempt.status:
       - Objective-only: EVALUATED + FINAL result.
       - Contains descriptive: SUBMITTED + PENDING result.
    """
    if scoring_policy is None:
        raise ValueError("A ScoringPolicy must be explicitly provided.")

    attempt.submitted_at = now
    attempt.submission_reason = submission_reason

    items = list(attempt.items.all().order_by("presentation_order"))
    pinned_ids = [item.question_version_id for item in items]

    answer_keys = {}
    if question_bank_port is not None:
        answer_keys = question_bank_port.get_objective_answer_keys(pinned_ids)

    # Evaluate each item
    for item in items:
        answer_key = answer_keys.get(item.question_version_id)
        response = item.response

        # If no answer key or marked DESCRIPTIVE, treat as descriptive
        if answer_key is None or answer_key.question_type == "DESCRIPTIVE":
            AttemptEvaluation.objects.create(
                attempt_item=item,
                evaluation_state=EvaluationState.PENDING_EVALUATION,
                marks_awarded=Decimal("0.0000"),
                marks_deducted=Decimal("0.0000"),
                evaluated_at=None,
                evaluator_id=None,
            )
            continue

        # Objective item evaluation
        if response.answer_state == AnswerState.UNANSWERED:
            AttemptEvaluation.objects.create(
                attempt_item=item,
                evaluation_state=EvaluationState.UNATTEMPTED,
                marks_awarded=Decimal("0.0000"),
                marks_deducted=Decimal("0.0000"),
                evaluated_at=None,
                evaluator_id=None,
            )
            continue

        # Answered objective item
        is_correct = False
        q_type = answer_key.question_type

        if q_type in ("MCQ", "MULTIPLE_SELECT"):
            selected_choice_ids = set(response.choices.values_list("choice_id", flat=True))
            is_correct = (selected_choice_ids == answer_key.correct_choice_ids)
        elif q_type == "TRUE_FALSE":
            is_correct = (response.boolean_response == answer_key.correct_boolean)
        elif q_type == "ASSERTION_REASON":
            is_correct = (response.assertion_reason_response == answer_key.correct_assertion_reason)
        elif q_type == "MATCH_FOLLOWING":
            student_pairs = {m.left_item_id: m.right_item_id for m in response.matches.all()}
            is_correct = (student_pairs == answer_key.correct_match_pairs)

        if is_correct:
            AttemptEvaluation.objects.create(
                attempt_item=item,
                evaluation_state=EvaluationState.CORRECT,
                marks_awarded=item.allocated_marks,
                marks_deducted=Decimal("0.0000"),
                evaluated_at=now,
                evaluator_id=None,
            )
        else:
            AttemptEvaluation.objects.create(
                attempt_item=item,
                evaluation_state=EvaluationState.INCORRECT,
                marks_awarded=Decimal("0.0000"),
                marks_deducted=item.allocated_penalty,
                evaluated_at=now,
                evaluator_id=None,
            )

    # Recalculate result aggregate and section records
    return recalculate_attempt_result(
        attempt=attempt,
        scoring_policy=scoring_policy,
        now=now,
    )


def recalculate_attempt_result(
    *,
    attempt: Attempt,
    scoring_policy: ScoringPolicy,
    now: datetime,
) -> tuple[Attempt, AttemptResult]:
    """
    Recalculates aggregate score, section scores, counters, and transitions
    the Attempt and AttemptResult lifecycles based on pending evaluations.
    """
    items = list(attempt.items.all().order_by("presentation_order"))
    evaluations = list(AttemptEvaluation.objects.filter(attempt_item__attempt=attempt))
    total_questions = len(evaluations)
    correct_questions = sum(1 for e in evaluations if e.evaluation_state == EvaluationState.CORRECT)
    incorrect_questions = sum(1 for e in evaluations if e.evaluation_state == EvaluationState.INCORRECT)
    partially_correct_questions = sum(1 for e in evaluations if e.evaluation_state == EvaluationState.PARTIALLY_CORRECT)
    attempted_questions = correct_questions + incorrect_questions + partially_correct_questions
    unanswered_questions = sum(1 for e in evaluations if e.evaluation_state == EvaluationState.UNATTEMPTED)
    pending_evaluation_questions = sum(1 for e in evaluations if e.evaluation_state == EvaluationState.PENDING_EVALUATION)

    raw_score = sum((e.marks_awarded - e.marks_deducted) for e in evaluations)
    maximum_score = sum(item.allocated_marks for item in items)

    score, percentage = scoring_policy.calculate_score(raw_score, maximum_score)

    if pending_evaluation_questions == 0:
        result_status = AttemptResultStatus.FINAL
        finalized_at = now
        attempt.status = AttemptStatus.EVALUATED
    else:
        result_status = AttemptResultStatus.PENDING
        finalized_at = None
        attempt.status = AttemptStatus.SUBMITTED

    attempt_result, _ = AttemptResult.objects.select_for_update().update_or_create(
        attempt=attempt,
        defaults={
            "status": result_status,
            "raw_score": raw_score.quantize(Decimal("0.0001")),
            "score": score,
            "maximum_score": maximum_score.quantize(Decimal("0.01")),
            "percentage": percentage,
            "total_questions": total_questions,
            "attempted_questions": attempted_questions,
            "correct_questions": correct_questions,
            "incorrect_questions": incorrect_questions,
            "partially_correct_questions": partially_correct_questions,
            "unanswered_questions": unanswered_questions,
            "pending_evaluation_questions": pending_evaluation_questions,
            "finalized_at": finalized_at,
        },
    )

    # Section-level aggregation
    sections_map = defaultdict(list)
    for item in items:
        if item.assessment_section_id is not None:
            sections_map[item.assessment_section_id].append(item)

    for section_id, sec_items in sections_map.items():
        sec_item_ids = {i.id for i in sec_items}
        sec_evals = [e for e in evaluations if e.attempt_item_id in sec_item_ids]

        sec_correct = sum(1 for e in sec_evals if e.evaluation_state == EvaluationState.CORRECT)
        sec_incorrect = sum(1 for e in sec_evals if e.evaluation_state == EvaluationState.INCORRECT)
        sec_partial = sum(1 for e in sec_evals if e.evaluation_state == EvaluationState.PARTIALLY_CORRECT)
        sec_attempted = sec_correct + sec_incorrect + sec_partial
        sec_unanswered = sum(1 for e in sec_evals if e.evaluation_state == EvaluationState.UNATTEMPTED)
        sec_pending = sum(1 for e in sec_evals if e.evaluation_state == EvaluationState.PENDING_EVALUATION)

        sec_raw = sum((e.marks_awarded - e.marks_deducted) for e in sec_evals)
        sec_max = sum(i.allocated_marks for i in sec_items)
        sec_score, _ = scoring_policy.calculate_score(sec_raw, sec_max)
        sec_order = min(i.presentation_order for i in sec_items)

        AttemptSectionResult.objects.update_or_create(
            attempt_result=attempt_result,
            assessment_section_id=section_id,
            defaults={
                "section_title_snapshot": f"Section {sec_order}",
                "section_order_snapshot": max(1, sec_order),
                "score": sec_score,
                "maximum_score": sec_max.quantize(Decimal("0.01")),
                "attempted_questions": sec_attempted,
                "correct_questions": sec_correct,
                "incorrect_questions": sec_incorrect,
                "partially_correct_questions": sec_partial,
                "unanswered_questions": sec_unanswered,
                "pending_evaluation_questions": sec_pending,
            },
        )

    attempt.save()
    return attempt, attempt_result


def execute_timeout_submission(
    attempt: Attempt,
    now: datetime,
    scoring_policy: ScoringPolicy,
    question_bank_port: QuestionBankPort | None = None,
) -> tuple[Attempt, AttemptResult]:
    """
    Delegate timeout auto-submission to the common submission workflow.
    """
    return execute_submission(
        attempt=attempt,
        now=now,
        scoring_policy=scoring_policy,
        submission_reason=SubmissionReason.TIMEOUT,
        question_bank_port=question_bank_port,
    )
