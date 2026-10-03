import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from django.contrib.auth.models import Group

from apps.attempts.application import evaluate_descriptive_item
from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    InvalidAttemptStateError,
    InvalidEvaluationError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptResponse,
    AttemptResult,
    AttemptSectionResult,
    AttemptStatus,
    EvaluationState,
    ScoreFloorPolicy,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.attempts.ports.question_bank import ObjectiveAnswerKeyDTO, QuestionBankPort
from apps.attempts.services.scoring import ZeroFloorTotalScoringPolicy


class MockQuestionBankPort(QuestionBankPort):
    def __init__(self, key_map=None):
        self.key_map = key_map or {}

    def get_objective_answer_keys(self, pinned_version_ids):
        return {vid: self.key_map[vid] for vid in pinned_version_ids if vid in self.key_map}


@pytest.mark.django_db
class TestDescriptiveEvaluationUseCase:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.fixed_now = datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.eval_time = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.student_id = uuid.uuid4()
        self.superadmin_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()
        self.paper_id = uuid.uuid4()
        self.section_id = uuid.uuid4()

        self.superadmin_auth = AuthorizationContext(
            actor_id=self.superadmin_id,
            is_student=False,
            is_superadmin=True,
        )
        self.student_auth = AuthorizationContext(
            actor_id=self.student_id,
            is_student=True,
            is_superadmin=False,
        )
        self.unauthorized_auth = AuthorizationContext(
            actor_id=self.other_user_id,
            is_student=False,
            is_superadmin=False,
        )

        # Submitted attempt with 1 objective item + 2 descriptive items
        self.attempt = Attempt.objects.create(
            student_id=self.student_id,
            assessment_paper_id=self.paper_id,
            attempt_number=1,
            duration_seconds=3600,
            started_at=self.fixed_now,
            expires_at=self.fixed_now,
            submitted_at=self.fixed_now,
            submission_reason="MANUAL",
            status=AttemptStatus.SUBMITTED,
            score_floor_policy=ScoreFloorPolicy.ZERO_FLOOR_TOTAL,
        )

        # Objective item (Item 1): MCQ (allocated 2.0000 marks, correct)
        self.q1_ver = uuid.uuid4()
        self.item_obj = AttemptItem.objects.create(
            attempt=self.attempt,
            paper_item_id=uuid.uuid4(),
            assessment_section_id=self.section_id,
            question_id=uuid.uuid4(),
            question_version_id=self.q1_ver,
            presentation_order=1,
            allocated_marks=Decimal("2.0000"),
            allocated_penalty=Decimal("0.5000"),
        )
        AttemptResponse.objects.create(
            attempt_item=self.item_obj,
            answer_state=AnswerState.ANSWERED,
        )
        AttemptEvaluation.objects.create(
            attempt_item=self.item_obj,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("2.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=self.fixed_now,
            evaluator_id=None,
        )

        # Descriptive item 1 (Item 2): allocated 5.0000 marks, PENDING_EVALUATION
        self.q2_ver = uuid.uuid4()
        self.item_desc1 = AttemptItem.objects.create(
            attempt=self.attempt,
            paper_item_id=uuid.uuid4(),
            assessment_section_id=self.section_id,
            question_id=uuid.uuid4(),
            question_version_id=self.q2_ver,
            presentation_order=2,
            allocated_marks=Decimal("5.0000"),
            allocated_penalty=Decimal("0.0000"),
        )
        AttemptResponse.objects.create(
            attempt_item=self.item_desc1,
            answer_state=AnswerState.ANSWERED,
            text_response="This is a detailed descriptive essay answer.",
        )
        self.eval_desc1 = AttemptEvaluation.objects.create(
            attempt_item=self.item_desc1,
            evaluation_state=EvaluationState.PENDING_EVALUATION,
            marks_awarded=Decimal("0.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=None,
            evaluator_id=None,
        )

        # Descriptive item 2 (Item 3): allocated 10.0000 marks, PENDING_EVALUATION
        self.q3_ver = uuid.uuid4()
        self.item_desc2 = AttemptItem.objects.create(
            attempt=self.attempt,
            paper_item_id=uuid.uuid4(),
            assessment_section_id=self.section_id,
            question_id=uuid.uuid4(),
            question_version_id=self.q3_ver,
            presentation_order=3,
            allocated_marks=Decimal("10.0000"),
            allocated_penalty=Decimal("0.0000"),
        )
        AttemptResponse.objects.create(
            attempt_item=self.item_desc2,
            answer_state=AnswerState.ANSWERED,
            text_response="Another descriptive answer.",
        )
        self.eval_desc2 = AttemptEvaluation.objects.create(
            attempt_item=self.item_desc2,
            evaluation_state=EvaluationState.PENDING_EVALUATION,
            marks_awarded=Decimal("0.0000"),
            marks_deducted=Decimal("0.0000"),
            evaluated_at=None,
            evaluator_id=None,
        )

        # Initial AttemptResult
        self.result = AttemptResult.objects.create(
            attempt=self.attempt,
            status=AttemptResultStatus.PENDING,
            raw_score=Decimal("2.0000"),
            score=Decimal("2.00"),
            maximum_score=Decimal("17.00"),
            percentage=Decimal("11.76"),
            total_questions=3,
            attempted_questions=1,
            correct_questions=1,
            incorrect_questions=0,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=2,
            finalized_at=None,
        )
        AttemptSectionResult.objects.create(
            attempt_result=self.result,
            assessment_section_id=self.section_id,
            section_title_snapshot="Section 1",
            section_order_snapshot=1,
            score=Decimal("2.00"),
            maximum_score=Decimal("17.00"),
            attempted_questions=1,
            correct_questions=1,
            incorrect_questions=0,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=2,
        )

        self.mock_qb_port = MockQuestionBankPort({
            self.q1_ver: ObjectiveAnswerKeyDTO(
                question_version_id=self.q1_ver,
                question_type="MCQ",
                correct_choice_ids={uuid.uuid4()},
                correct_boolean=None,
                correct_assertion_reason=None,
                correct_match_pairs={},
            ),
            self.q2_ver: ObjectiveAnswerKeyDTO(
                question_version_id=self.q2_ver,
                question_type="DESCRIPTIVE",
                correct_choice_ids=set(),
                correct_boolean=None,
                correct_assertion_reason=None,
                correct_match_pairs={},
            ),
            self.q3_ver: ObjectiveAnswerKeyDTO(
                question_version_id=self.q3_ver,
                question_type="DESCRIPTIVE",
                correct_choice_ids=set(),
                correct_boolean=None,
                correct_assertion_reason=None,
                correct_match_pairs={},
            ),
        })

    def test_only_authorized_superadmin_can_evaluate(self):
        # Student cannot evaluate
        with pytest.raises(AttemptAuthorizationError):
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="CORRECT",
                authorization=self.student_auth,
                question_bank_port=self.mock_qb_port,
            )

        # Unauthorized actor cannot evaluate
        with pytest.raises(AttemptAuthorizationError):
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="CORRECT",
                authorization=self.unauthorized_auth,
                question_bank_port=self.mock_qb_port,
            )

    def test_correct_evaluation_awards_full_marks_and_recalculates(self):
        attempt, item, evaluation, result = evaluate_descriptive_item(
            attempt_id=self.attempt.id,
            attempt_item_id=self.item_desc1.id,
            evaluation_state="CORRECT",
            authorization=self.superadmin_auth,
            evaluation_comments="Excellent explanation.",
            question_bank_port=self.mock_qb_port,
            now=self.eval_time,
        )

        assert evaluation.evaluation_state == EvaluationState.CORRECT
        assert evaluation.marks_awarded == Decimal("5.0000")
        assert evaluation.marks_deducted == Decimal("0.0000")
        assert evaluation.net_marks == Decimal("5.0000")
        assert evaluation.evaluator_id == self.superadmin_id
        assert evaluation.evaluated_at == self.eval_time
        assert evaluation.evaluation_comments == "Excellent explanation."

        # Still 1 pending evaluation remaining (item_desc2)
        assert result.status == AttemptResultStatus.PENDING
        assert attempt.status == AttemptStatus.SUBMITTED
        assert result.pending_evaluation_questions == 1
        assert result.correct_questions == 2  # obj + desc1
        assert result.score == Decimal("7.00")  # 2.00 + 5.00

    def test_partially_correct_evaluation(self):
        attempt, item, evaluation, result = evaluate_descriptive_item(
            attempt_id=self.attempt.id,
            attempt_item_id=self.item_desc1.id,
            evaluation_state="PARTIALLY_CORRECT",
            marks_awarded=Decimal("3.5000"),
            authorization=self.superadmin_auth,
            evaluation_comments="Good attempt, missing conclusion.",
            question_bank_port=self.mock_qb_port,
            now=self.eval_time,
        )

        assert evaluation.evaluation_state == EvaluationState.PARTIALLY_CORRECT
        assert evaluation.marks_awarded == Decimal("3.5000")
        assert evaluation.net_marks == Decimal("3.5000")
        assert result.partially_correct_questions == 1
        assert result.score == Decimal("5.50")  # 2.00 + 3.50

    def test_incorrect_evaluation(self):
        attempt, item, evaluation, result = evaluate_descriptive_item(
            attempt_id=self.attempt.id,
            attempt_item_id=self.item_desc1.id,
            evaluation_state="INCORRECT",
            authorization=self.superadmin_auth,
            evaluation_comments="Factually incorrect.",
            question_bank_port=self.mock_qb_port,
            now=self.eval_time,
        )

        assert evaluation.evaluation_state == EvaluationState.INCORRECT
        assert evaluation.marks_awarded == Decimal("0.0000")
        assert result.incorrect_questions == 1
        assert result.score == Decimal("2.00")  # unchanged

    def test_partially_correct_strictly_between_zero_and_allocated_marks(self):
        # 0 awarded rejected
        with pytest.raises(InvalidEvaluationError) as cm1:
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="PARTIALLY_CORRECT",
                marks_awarded=Decimal("0.0000"),
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )
        assert "strictly between 0 and allocated marks" in str(cm1.value)

        # Full allocated marks awarded rejected for PARTIALLY_CORRECT
        with pytest.raises(InvalidEvaluationError) as cm2:
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="PARTIALLY_CORRECT",
                marks_awarded=Decimal("5.0000"),
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )
        assert "strictly between 0 and allocated marks" in str(cm2.value)

    def test_invalid_marks_boundaries(self):
        # Marks awarded exceeds allocated
        with pytest.raises(InvalidEvaluationError):
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="CORRECT",
                marks_awarded=Decimal("6.0000"),  # allocated is 5
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )

        # Negative marks awarded
        with pytest.raises(InvalidEvaluationError):
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="PARTIALLY_CORRECT",
                marks_awarded=Decimal("-1.0000"),
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )

        # Negative marks deducted
        with pytest.raises(InvalidEvaluationError):
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="CORRECT",
                marks_deducted=Decimal("-0.5000"),
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )

    def test_cannot_evaluate_objective_item(self):
        with pytest.raises(InvalidEvaluationError) as cm:
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_obj.id,
                evaluation_state="CORRECT",
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )
        assert "Only descriptive items can be manually evaluated" in str(cm.value)

    def test_cannot_evaluate_already_evaluated_item(self):
        # Evaluate item 1
        evaluate_descriptive_item(
            attempt_id=self.attempt.id,
            attempt_item_id=self.item_desc1.id,
            evaluation_state="CORRECT",
            authorization=self.superadmin_auth,
            question_bank_port=self.mock_qb_port,
        )

        # Re-evaluating raises error
        with pytest.raises(InvalidEvaluationError) as cm:
            evaluate_descriptive_item(
                attempt_id=self.attempt.id,
                attempt_item_id=self.item_desc1.id,
                evaluation_state="CORRECT",
                authorization=self.superadmin_auth,
                question_bank_port=self.mock_qb_port,
            )
        assert "Item is not pending evaluation" in str(cm.value)

    def test_final_transition_when_all_descriptive_items_evaluated(self):
        # 1. Evaluate first descriptive item
        evaluate_descriptive_item(
            attempt_id=self.attempt.id,
            attempt_item_id=self.item_desc1.id,
            evaluation_state="CORRECT",
            authorization=self.superadmin_auth,
            question_bank_port=self.mock_qb_port,
            now=self.eval_time,
        )

        # 2. Evaluate second descriptive item
        attempt, _, _, result = evaluate_descriptive_item(
            attempt_id=self.attempt.id,
            attempt_item_id=self.item_desc2.id,
            evaluation_state="PARTIALLY_CORRECT",
            marks_awarded=Decimal("6.0000"),
            authorization=self.superadmin_auth,
            question_bank_port=self.mock_qb_port,
            now=self.eval_time,
        )

        # Zero pending evaluations remain -> FINAL and EVALUATED!
        assert result.pending_evaluation_questions == 0
        assert result.status == AttemptResultStatus.FINAL
        assert result.finalized_at == self.eval_time
        assert attempt.status == AttemptStatus.EVALUATED

        # Total score: 2 (obj) + 5 (desc1) + 6 (desc2) = 13.00 out of 17.00
        assert result.score == Decimal("13.00")
        assert result.maximum_score == Decimal("17.00")
        assert result.correct_questions == 2
        assert result.partially_correct_questions == 1
        assert result.attempted_questions == 3

        # Check section result updated
        sec_res = AttemptSectionResult.objects.get(attempt_result=result)
        assert sec_res.score == Decimal("13.00")
        assert sec_res.pending_evaluation_questions == 0
        assert sec_res.attempted_questions == 3
