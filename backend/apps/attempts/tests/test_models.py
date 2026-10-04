import uuid
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.attempts.models import (
    AnswerState,
    AssertionReasonResponse,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptItemChoice,
    AttemptResponse,
    AttemptResponseChoice,
    AttemptResponseMatch,
    AttemptResult,
    AttemptResultStatus,
    AttemptSectionResult,
    AttemptStatus,
    EvaluationState,
    ScoreFloorPolicy,
    SubmissionReason,
)


@pytest.fixture
def student_id():
    return uuid.uuid4()


@pytest.fixture
def paper_id():
    return uuid.uuid4()


@pytest.fixture
def attempt(student_id, paper_id):
    now = timezone.now()
    return Attempt.objects.create(
        student_id=student_id,
        assessment_paper_id=paper_id,
        attempt_number=1,
        duration_seconds=3600,
        started_at=now,
        expires_at=now + timezone.timedelta(seconds=3600),
    )


@pytest.fixture
def attempt_item(attempt):
    return AttemptItem.objects.create(
        attempt=attempt,
        paper_item_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        question_version_id=uuid.uuid4(),
        presentation_order=1,
        allocated_marks=Decimal("2.0000"),
        allocated_penalty=Decimal("0.6667"),
    )


@pytest.fixture
def attempt_response(attempt_item):
    return AttemptResponse.objects.create(
        attempt_item=attempt_item,
        answer_state=AnswerState.UNANSWERED,
    )


@pytest.fixture
def attempt_result(attempt):
    return AttemptResult.objects.create(
        attempt=attempt,
        status=AttemptResultStatus.PENDING,
        raw_score=Decimal("0.0000"),
        score=Decimal("0.00"),
        maximum_score=Decimal("100.00"),
        percentage=Decimal("0.00"),
        total_questions=10,
        attempted_questions=0,
        correct_questions=0,
        incorrect_questions=0,
        partially_correct_questions=0,
        unanswered_questions=10,
        pending_evaluation_questions=0,
    )


# =============================================================================
# 1. ATTEMPT TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptModel:
    def test_valid_creation(self, attempt, student_id, paper_id):
        assert isinstance(attempt.id, uuid.UUID)
        assert attempt.student_id == student_id
        assert attempt.assessment_paper_id == paper_id
        assert attempt.attempt_number == 1
        assert attempt.status == AttemptStatus.IN_PROGRESS
        assert attempt.scoring_policy_version == "v1"
        assert attempt.score_floor_policy == ScoreFloorPolicy.UNRESTRICTED
        assert attempt.submission_reason is None
        assert attempt.cancelled_at is None
        assert attempt.cancelled_by is None
        assert attempt.cancellation_reason is None

    def test_unique_student_paper_attempt_number(self, student_id, paper_id, attempt):
        now = timezone.now()
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Attempt.objects.create(
                    student_id=student_id,
                    assessment_paper_id=paper_id,
                    attempt_number=1,  # Duplicate attempt_number
                    duration_seconds=3600,
                    started_at=now,
                    expires_at=now + timezone.timedelta(seconds=3600),
                )

    def test_retake_with_different_attempt_number_succeeds(self, student_id, paper_id, attempt):
        now = timezone.now()
        retake = Attempt.objects.create(
            student_id=student_id,
            assessment_paper_id=paper_id,
            attempt_number=2,
            duration_seconds=3600,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=3600),
        )
        assert retake.attempt_number == 2

    def test_different_paper_same_student_succeeds(self, student_id, attempt):
        now = timezone.now()
        other_paper_id = uuid.uuid4()
        other_attempt = Attempt.objects.create(
            student_id=student_id,
            assessment_paper_id=other_paper_id,
            attempt_number=1,
            duration_seconds=3600,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=3600),
        )
        assert other_attempt.assessment_paper_id == other_paper_id

    def test_cancellation_metadata_valid(self, student_id, paper_id):
        now = timezone.now()
        admin_id = uuid.uuid4()
        cancelled_attempt = Attempt(
            student_id=student_id,
            assessment_paper_id=paper_id,
            attempt_number=1,
            status=AttemptStatus.CANCELLED,
            duration_seconds=1800,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=1800),
            cancelled_at=now,
            cancelled_by=admin_id,
            cancellation_reason="Student encountered technical issue.",
        )
        cancelled_attempt.full_clean()
        cancelled_attempt.save()
        assert cancelled_attempt.status == AttemptStatus.CANCELLED

    def test_cancellation_missing_metadata_rejected(self, student_id, paper_id):
        now = timezone.now()
        attempt = Attempt(
            student_id=student_id,
            assessment_paper_id=paper_id,
            attempt_number=1,
            status=AttemptStatus.CANCELLED,
            duration_seconds=1800,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=1800),
            cancelled_at=None,
            cancelled_by=None,
            cancellation_reason=None,
        )
        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_cancellation_empty_reason_rejected(self, student_id, paper_id):
        now = timezone.now()
        attempt = Attempt(
            student_id=student_id,
            assessment_paper_id=paper_id,
            attempt_number=1,
            status=AttemptStatus.CANCELLED,
            duration_seconds=1800,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=1800),
            cancelled_at=now,
            cancelled_by=uuid.uuid4(),
            cancellation_reason="   ",
        )
        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_non_cancelled_retaining_cancellation_metadata_rejected(self, student_id, paper_id):
        now = timezone.now()
        attempt = Attempt(
            student_id=student_id,
            assessment_paper_id=paper_id,
            attempt_number=1,
            status=AttemptStatus.IN_PROGRESS,
            duration_seconds=1800,
            started_at=now,
            expires_at=now + timezone.timedelta(seconds=1800),
            cancelled_at=now,
            cancelled_by=uuid.uuid4(),
            cancellation_reason="Premature cancellation data",
        )
        with pytest.raises(ValidationError):
            attempt.full_clean()

    def test_attempt_number_positive_constraint(self, student_id, paper_id):
        now = timezone.now()
        with pytest.raises((IntegrityError, ValidationError)):
            with transaction.atomic():
                Attempt.objects.create(
                    student_id=student_id,
                    assessment_paper_id=paper_id,
                    attempt_number=0,  # Invalid
                    duration_seconds=3600,
                    started_at=now,
                    expires_at=now + timezone.timedelta(seconds=3600),
                )


# =============================================================================
# 2. ATTEMPT ITEM TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptItemModel:
    def test_valid_creation(self, attempt_item, attempt):
        assert isinstance(attempt_item.id, uuid.UUID)
        assert attempt_item.attempt == attempt
        assert attempt_item.presentation_order == 1
        assert attempt_item.allocated_marks == Decimal("2.0000")
        assert attempt_item.allocated_penalty == Decimal("0.6667")

    def test_unique_presentation_order_per_attempt(self, attempt, attempt_item):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptItem.objects.create(
                    attempt=attempt,
                    paper_item_id=uuid.uuid4(),
                    question_id=uuid.uuid4(),
                    question_version_id=uuid.uuid4(),
                    presentation_order=1,  # Duplicate presentation_order
                    allocated_marks=Decimal("1.0000"),
                    allocated_penalty=Decimal("0.0000"),
                )

    def test_unique_paper_item_per_attempt(self, attempt, attempt_item):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptItem.objects.create(
                    attempt=attempt,
                    paper_item_id=attempt_item.paper_item_id,  # Duplicate paper_item_id
                    question_id=uuid.uuid4(),
                    question_version_id=uuid.uuid4(),
                    presentation_order=2,
                    allocated_marks=Decimal("1.0000"),
                    allocated_penalty=Decimal("0.0000"),
                )

    def test_positive_presentation_order_constraint(self, attempt):
        item = AttemptItem(
            attempt=attempt,
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            presentation_order=0,  # Invalid
            allocated_marks=Decimal("1.0000"),
            allocated_penalty=Decimal("0.0000"),
        )
        with pytest.raises((ValidationError, IntegrityError)):
            item.full_clean()
            item.save()

    def test_negative_allocated_marks_rejected(self, attempt):
        item = AttemptItem(
            attempt=attempt,
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            presentation_order=2,
            allocated_marks=Decimal("-1.0000"),  # Invalid
            allocated_penalty=Decimal("0.0000"),
        )
        with pytest.raises((ValidationError, IntegrityError)):
            item.full_clean()
            item.save()

    def test_negative_allocated_penalty_rejected(self, attempt):
        item = AttemptItem(
            attempt=attempt,
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            presentation_order=2,
            allocated_marks=Decimal("1.0000"),
            allocated_penalty=Decimal("-0.3333"),  # Invalid
        )
        with pytest.raises((ValidationError, IntegrityError)):
            item.full_clean()
            item.save()


# =============================================================================
# 3. ATTEMPT ITEM CHOICE TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptItemChoiceModel:
    def test_valid_creation(self, attempt_item):
        choice_id = uuid.uuid4()
        aic = AttemptItemChoice.objects.create(
            attempt_item=attempt_item,
            choice_id=choice_id,
            presented_position=1,
        )
        assert isinstance(aic.id, uuid.UUID)
        assert aic.presented_position == 1

    def test_unique_presented_position_per_item(self, attempt_item):
        AttemptItemChoice.objects.create(
            attempt_item=attempt_item,
            choice_id=uuid.uuid4(),
            presented_position=1,
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptItemChoice.objects.create(
                    attempt_item=attempt_item,
                    choice_id=uuid.uuid4(),
                    presented_position=1,  # Duplicate position
                )

    def test_unique_choice_id_per_item(self, attempt_item):
        choice_id = uuid.uuid4()
        AttemptItemChoice.objects.create(
            attempt_item=attempt_item,
            choice_id=choice_id,
            presented_position=1,
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptItemChoice.objects.create(
                    attempt_item=attempt_item,
                    choice_id=choice_id,  # Duplicate choice
                    presented_position=2,
                )

    def test_positive_presented_position(self, attempt_item):
        choice = AttemptItemChoice(
            attempt_item=attempt_item,
            choice_id=uuid.uuid4(),
            presented_position=0,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            choice.full_clean()
            choice.save()


# =============================================================================
# 4. ATTEMPT RESPONSE TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptResponseModel:
    def test_one_to_one_response_per_attempt_item(self, attempt_item, attempt_response):
        assert attempt_response.attempt_item == attempt_item
        assert attempt_response.answer_state == AnswerState.UNANSWERED

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptResponse.objects.create(
                    attempt_item=attempt_item,  # Duplicate response for item
                    answer_state=AnswerState.ANSWERED,
                )

    def test_response_answering_and_clearing(self, attempt_response):
        attempt_response.answer_state = AnswerState.ANSWERED
        attempt_response.boolean_response = True
        attempt_response.save()

        attempt_response.refresh_from_db()
        assert attempt_response.answer_state == AnswerState.ANSWERED
        assert attempt_response.boolean_response is True

        # Clear answer
        attempt_response.answer_state = AnswerState.UNANSWERED
        attempt_response.boolean_response = None
        attempt_response.save()

        attempt_response.refresh_from_db()
        assert attempt_response.answer_state == AnswerState.UNANSWERED
        assert attempt_response.boolean_response is None


# =============================================================================
# 5. ATTEMPT RESPONSE CHOICE TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptResponseChoiceModel:
    def test_valid_creation(self, attempt_response):
        choice_id = uuid.uuid4()
        arc = AttemptResponseChoice.objects.create(
            attempt_response=attempt_response,
            choice_id=choice_id,
        )
        assert isinstance(arc.id, uuid.UUID)

    def test_duplicate_choice_selection_rejected(self, attempt_response):
        choice_id = uuid.uuid4()
        AttemptResponseChoice.objects.create(
            attempt_response=attempt_response,
            choice_id=choice_id,
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptResponseChoice.objects.create(
                    attempt_response=attempt_response,
                    choice_id=choice_id,  # Duplicate
                )


# =============================================================================
# 6. ATTEMPT RESPONSE MATCH TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptResponseMatchModel:
    def test_valid_creation(self, attempt_response):
        left_id = uuid.uuid4()
        right_id = uuid.uuid4()
        arm = AttemptResponseMatch.objects.create(
            attempt_response=attempt_response,
            left_item_id=left_id,
            right_item_id=right_id,
        )
        assert isinstance(arm.id, uuid.UUID)

    def test_duplicate_left_mapping_rejected(self, attempt_response):
        left_id = uuid.uuid4()
        AttemptResponseMatch.objects.create(
            attempt_response=attempt_response,
            left_item_id=left_id,
            right_item_id=uuid.uuid4(),
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptResponseMatch.objects.create(
                    attempt_response=attempt_response,
                    left_item_id=left_id,  # Duplicate left item
                    right_item_id=uuid.uuid4(),
                )

    def test_duplicate_right_mapping_rejected(self, attempt_response):
        right_id = uuid.uuid4()
        AttemptResponseMatch.objects.create(
            attempt_response=attempt_response,
            left_item_id=uuid.uuid4(),
            right_item_id=right_id,
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptResponseMatch.objects.create(
                    attempt_response=attempt_response,
                    left_item_id=uuid.uuid4(),
                    right_item_id=right_id,  # Duplicate right item
                )


# =============================================================================
# 7. ATTEMPT EVALUATION TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptEvaluationModel:
    def test_one_evaluation_per_attempt_item(self, attempt_item):
        now = timezone.now()
        eval1 = AttemptEvaluation.objects.create(
            attempt_item=attempt_item,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("2.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=now,
        )
        assert eval1.net_marks == Decimal("2.0000")

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptEvaluation.objects.create(
                    attempt_item=attempt_item,  # Duplicate evaluation
                    evaluation_state=EvaluationState.INCORRECT,
                    marks_awarded=Decimal("0.0000"),
                    marks_deducted=Decimal("0.6667"),
                    evaluated_at=now,
                )

    def test_negative_marks_rejected(self, attempt_item):
        now = timezone.now()
        e = AttemptEvaluation(
            attempt_item=attempt_item,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("-1.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=now,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            e.full_clean()
            e.save()

    def test_pending_evaluation_requires_null_evaluated_at_and_evaluator_id(self, attempt_item):
        now = timezone.now()
        # Invalid: PENDING_EVALUATION with evaluated_at
        e = AttemptEvaluation(
            attempt_item=attempt_item,
            evaluation_state=EvaluationState.PENDING_EVALUATION,
            marks_awarded=Decimal("0.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=now,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            e.full_clean()
            e.save()

    def test_unattempted_requires_null_evaluated_at_and_evaluator_id(self, attempt_item):
        now = timezone.now()
        # Invalid: UNATTEMPTED with evaluator_id
        e = AttemptEvaluation(
            attempt_item=attempt_item,
            evaluation_state=EvaluationState.UNATTEMPTED,
            marks_awarded=Decimal("0.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluator_id=uuid.uuid4(),
        )
        with pytest.raises((ValidationError, IntegrityError)):
            e.full_clean()
            e.save()

    def test_correct_requires_non_null_evaluated_at(self, attempt_item):
        # Invalid: CORRECT without evaluated_at
        e = AttemptEvaluation(
            attempt_item=attempt_item,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("2.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=None,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            e.full_clean()
            e.save()

    def test_partially_correct_requires_evaluator_id_and_evaluated_at(self, attempt_item):
        now = timezone.now()
        # Invalid: PARTIALLY_CORRECT without evaluator_id
        e = AttemptEvaluation(
            attempt_item=attempt_item,
            evaluation_state=EvaluationState.PARTIALLY_CORRECT,
            marks_awarded=Decimal("1.5000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=now,
            evaluator_id=None,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            e.full_clean()
            e.save()

        # Valid with evaluator_id
        admin_id = uuid.uuid4()
        e.evaluator_id = admin_id
        e.full_clean()
        e.save()
        assert e.evaluation_state == EvaluationState.PARTIALLY_CORRECT
        assert e.evaluator_id == admin_id


# =============================================================================
# 8. ATTEMPT RESULT TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptResultModel:
    def test_valid_pending_creation(self, attempt_result, attempt):
        assert attempt_result.attempt == attempt
        assert attempt_result.status == AttemptResultStatus.PENDING
        assert attempt_result.finalized_at is None
        assert attempt_result.total_questions == 10
        assert attempt_result.attempted_questions == 0
        assert attempt_result.unanswered_questions == 10

    def test_attempted_checksum_constraint(self, attempt):
        # Invalid: attempted (5) != correct (2) + incorrect (2) + partially (0) = 4
        res = AttemptResult(
            attempt=attempt,
            status=AttemptResultStatus.PENDING,
            total_questions=10,
            attempted_questions=5,  # Mismatch!
            correct_questions=2,
            incorrect_questions=2,
            partially_correct_questions=0,
            unanswered_questions=5,
            pending_evaluation_questions=0,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            res.full_clean()
            res.save()

    def test_total_checksum_constraint_including_pending(self, attempt):
        # total (10) != attempted (4) + unanswered (4) + pending (1) = 9
        res = AttemptResult(
            attempt=attempt,
            status=AttemptResultStatus.PENDING,
            total_questions=10,  # Mismatch!
            attempted_questions=4,
            correct_questions=2,
            incorrect_questions=2,
            partially_correct_questions=0,
            unanswered_questions=4,
            pending_evaluation_questions=1,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            res.full_clean()
            res.save()

    def test_final_result_requires_zero_pending_and_finalized_at(self, attempt):
        now = timezone.now()
        # Invalid: FINAL with pending > 0
        res = AttemptResult(
            attempt=attempt,
            status=AttemptResultStatus.FINAL,
            total_questions=10,
            attempted_questions=9,
            correct_questions=6,
            incorrect_questions=2,
            partially_correct_questions=1,
            unanswered_questions=0,
            pending_evaluation_questions=1,  # Invalid for FINAL!
            finalized_at=now,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            res.full_clean()
            res.save()

        # Invalid: FINAL without finalized_at
        res.pending_evaluation_questions = 0
        res.attempted_questions = 10
        res.correct_questions = 7
        res.finalized_at = None
        with pytest.raises((ValidationError, IntegrityError)):
            res.full_clean()
            res.save()

        # Valid FINAL
        res.finalized_at = now
        res.full_clean()
        res.save()
        assert res.status == AttemptResultStatus.FINAL

    def test_pending_or_void_cannot_retain_finalized_at(self, attempt):
        now = timezone.now()
        res = AttemptResult(
            attempt=attempt,
            status=AttemptResultStatus.PENDING,
            total_questions=10,
            attempted_questions=5,
            correct_questions=3,
            incorrect_questions=2,
            partially_correct_questions=0,
            unanswered_questions=5,
            pending_evaluation_questions=0,
            finalized_at=now,  # Invalid for PENDING
        )
        with pytest.raises((ValidationError, IntegrityError)):
            res.full_clean()
            res.save()


# =============================================================================
# 9. ATTEMPT SECTION RESULT TESTS
# =============================================================================
@pytest.mark.django_db
class TestAttemptSectionResultModel:
    def test_valid_creation(self, attempt_result):
        sec_id = uuid.uuid4()
        asr = AttemptSectionResult.objects.create(
            attempt_result=attempt_result,
            assessment_section_id=sec_id,
            section_title_snapshot="General Science",
            section_order_snapshot=1,
            score=Decimal("15.00"),
            maximum_score=Decimal("20.00"),
            attempted_questions=8,
            correct_questions=6,
            incorrect_questions=2,
            partially_correct_questions=0,
            unanswered_questions=2,
            pending_evaluation_questions=0,
        )
        assert isinstance(asr.id, uuid.UUID)
        assert asr.section_order_snapshot == 1

    def test_unique_result_and_section_id(self, attempt_result):
        sec_id = uuid.uuid4()
        AttemptSectionResult.objects.create(
            attempt_result=attempt_result,
            assessment_section_id=sec_id,
            section_title_snapshot="General Science",
            section_order_snapshot=1,
            score=Decimal("15.00"),
            maximum_score=Decimal("20.00"),
            attempted_questions=5,
            correct_questions=5,
            incorrect_questions=0,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=0,
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttemptSectionResult.objects.create(
                    attempt_result=attempt_result,
                    assessment_section_id=sec_id,  # Duplicate section
                    section_title_snapshot="General Science Dupe",
                    section_order_snapshot=2,
                    score=Decimal("10.00"),
                    maximum_score=Decimal("20.00"),
                    attempted_questions=0,
                    correct_questions=0,
                    incorrect_questions=0,
                    partially_correct_questions=0,
                    unanswered_questions=0,
                    pending_evaluation_questions=0,
                )

    def test_attempted_checksum_constraint(self, attempt_result):
        # Mismatch: attempted (5) != correct (3) + incorrect (1) + partially (0) = 4
        asr = AttemptSectionResult(
            attempt_result=attempt_result,
            assessment_section_id=uuid.uuid4(),
            section_title_snapshot="Math",
            section_order_snapshot=1,
            score=Decimal("5.00"),
            maximum_score=Decimal("10.00"),
            attempted_questions=5,  # Mismatch!
            correct_questions=3,
            incorrect_questions=1,
            partially_correct_questions=0,
            unanswered_questions=5,
            pending_evaluation_questions=0,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            asr.full_clean()
            asr.save()

    def test_positive_section_order_constraint(self, attempt_result):
        asr = AttemptSectionResult(
            attempt_result=attempt_result,
            assessment_section_id=uuid.uuid4(),
            section_title_snapshot="Polity",
            section_order_snapshot=0,  # Invalid
            score=Decimal("0.00"),
            maximum_score=Decimal("10.00"),
            attempted_questions=0,
            correct_questions=0,
            incorrect_questions=0,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=0,
        )
        with pytest.raises((ValidationError, IntegrityError)):
            asr.full_clean()
            asr.save()
