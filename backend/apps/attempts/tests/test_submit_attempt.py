from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from django.test import TestCase

from apps.attempts.application.save_response import save_response
from apps.attempts.application.start_attempt import start_attempt
from apps.attempts.application.submit_attempt import submit_attempt
from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptNotFoundError,
    InvalidAttemptStateError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptResult,
    AttemptSectionResult,
    AttemptStatus,
    EvaluationState,
    SubmissionReason,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.attempts.ports.assessment import (
    DeliveryPayloadDTO,
    PaperChoiceDTO,
    PaperItemDTO,
    PaperMatchPairDTO,
)
from apps.attempts.ports.question_bank import ObjectiveAnswerKeyDTO
from apps.attempts.services.scoring import (
    UnrestrictedScoringPolicy,
    ZeroFloorSectionScoringPolicy,
    ZeroFloorTotalScoringPolicy,
)


class FakeAssessmentPaperPort:
    def __init__(self, payload: DeliveryPayloadDTO):
        self.payload = payload

    def get_paper_delivery_payload(self, paper_id: uuid.UUID, student_id: uuid.UUID) -> DeliveryPayloadDTO:
        return self.payload


class FakeQuestionBankPort:
    def __init__(self, keys_map: dict[uuid.UUID, ObjectiveAnswerKeyDTO]):
        self.keys_map = keys_map

    def get_objective_answer_keys(self, pinned_version_ids: list[uuid.UUID]) -> dict[uuid.UUID, ObjectiveAnswerKeyDTO]:
        return {vid: self.keys_map[vid] for vid in pinned_version_ids if vid in self.keys_map}


class SubmitAttemptUseCaseTests(TestCase):
    def setUp(self):
        self.student_id = uuid.uuid4()
        self.paper_id = uuid.uuid4()
        self.section_id = uuid.uuid4()
        self.auth_context = AuthorizationContext(
            actor_id=self.student_id,
            is_student=True,
            is_superadmin=False,
        )

        self.fixed_now = datetime(2026, 10, 3, 10, 0, 0, tzinfo=timezone.utc)

        # MCQ Item (Item 1)
        self.mcq_item_id = uuid.uuid4()
        self.mcq_qv_id = uuid.uuid4()
        self.choice_1a = uuid.uuid4()
        self.choice_1b = uuid.uuid4()

        # True/False Item (Item 2)
        self.tf_item_id = uuid.uuid4()
        self.tf_qv_id = uuid.uuid4()

        # Descriptive Item (Item 3)
        self.desc_item_id = uuid.uuid4()
        self.desc_qv_id = uuid.uuid4()

        # Mixed items payload
        self.mixed_items = [
            PaperItemDTO(
                paper_item_id=self.mcq_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.mcq_qv_id,
                question_type="MCQ",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=1,
                allocated_marks=Decimal("2.0000"),
                allocated_penalty=Decimal("0.6600"),
                choices=[
                    PaperChoiceDTO(choice_id=self.choice_1a, choice_text="A", presented_position=1),
                    PaperChoiceDTO(choice_id=self.choice_1b, choice_text="B", presented_position=2),
                ],
            ),
            PaperItemDTO(
                paper_item_id=self.tf_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.tf_qv_id,
                question_type="TRUE_FALSE",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=2,
                allocated_marks=Decimal("1.0000"),
                allocated_penalty=Decimal("0.3300"),
            ),
            PaperItemDTO(
                paper_item_id=self.desc_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.desc_qv_id,
                question_type="DESCRIPTIVE",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=3,
                allocated_marks=Decimal("5.0000"),
                allocated_penalty=Decimal("0.0000"),
            ),
        ]

        self.mixed_payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=self.mixed_items,
        )
        self.port = FakeAssessmentPaperPort(self.mixed_payload)

        # Answer keys
        self.qb_keys = {
            self.mcq_qv_id: ObjectiveAnswerKeyDTO(
                question_version_id=self.mcq_qv_id,
                question_type="MCQ",
                correct_choice_ids={self.choice_1a},
                correct_boolean=None,
                correct_assertion_reason=None,
                correct_match_pairs={},
            ),
            self.tf_qv_id: ObjectiveAnswerKeyDTO(
                question_version_id=self.tf_qv_id,
                question_type="TRUE_FALSE",
                correct_choice_ids=set(),
                correct_boolean=True,
                correct_assertion_reason=None,
                correct_match_pairs={},
            ),
        }
        self.qb_port = FakeQuestionBankPort(self.qb_keys)

        self.attempt = start_attempt(
            student_id=self.student_id,
            paper_id=self.paper_id,
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now,
        )
        self.items = list(self.attempt.items.order_by("presentation_order"))

    # --- NORMAL MANUAL SUBMISSION TESTS ---

    def test_normal_manual_submission_descriptive_containing(self):
        """
        Verify normal manual submission for an attempt containing descriptive items:
        - now < expires_at
        - status transitions to SUBMITTED
        - submission_reason is MANUAL
        - AttemptResult status is PENDING
        - finalized_at is None
        - exactly one evaluation per item
        - descriptive evaluation is PENDING_EVALUATION
        """
        # Answer MCQ correctly
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=self.items[0].id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
            now=self.fixed_now + timedelta(minutes=5),
        )

        submit_now = self.fixed_now + timedelta(minutes=15)
        attempt, result = submit_attempt(
            attempt_id=self.attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=submit_now,
        )

        self.assertEqual(attempt.status, AttemptStatus.SUBMITTED)
        self.assertEqual(attempt.submission_reason, SubmissionReason.MANUAL)
        self.assertEqual(attempt.submitted_at, submit_now)

        # Result checks
        self.assertEqual(result.status, AttemptResultStatus.PENDING)
        self.assertIsNone(result.finalized_at)
        self.assertEqual(result.total_questions, 3)
        self.assertEqual(result.attempted_questions, 1)
        self.assertEqual(result.correct_questions, 1)
        self.assertEqual(result.unanswered_questions, 1)
        self.assertEqual(result.pending_evaluation_questions, 1)

        # Evaluations check
        evals = list(AttemptEvaluation.objects.filter(attempt_item__attempt=attempt).order_by("attempt_item__presentation_order"))
        self.assertEqual(len(evals), 3)

        # Item 1 (MCQ) - CORRECT
        self.assertEqual(evals[0].evaluation_state, EvaluationState.CORRECT)
        self.assertEqual(evals[0].marks_awarded, Decimal("2.0000"))
        self.assertEqual(evals[0].marks_deducted, Decimal("0.0000"))
        self.assertEqual(evals[0].evaluated_at, submit_now)

        # Item 2 (TF) - UNATTEMPTED
        self.assertEqual(evals[1].evaluation_state, EvaluationState.UNATTEMPTED)
        self.assertEqual(evals[1].marks_awarded, Decimal("0.0000"))
        self.assertEqual(evals[1].marks_deducted, Decimal("0.0000"))
        self.assertIsNone(evals[1].evaluated_at)

        # Item 3 (Descriptive) - PENDING_EVALUATION
        self.assertEqual(evals[2].evaluation_state, EvaluationState.PENDING_EVALUATION)
        self.assertEqual(evals[2].marks_awarded, Decimal("0.0000"))
        self.assertEqual(evals[2].marks_deducted, Decimal("0.0000"))
        self.assertIsNone(evals[2].evaluated_at)
        self.assertIsNone(evals[2].evaluator_id)

        # Section result created
        sec_results = list(AttemptSectionResult.objects.filter(attempt_result=result))
        self.assertEqual(len(sec_results), 1)
        self.assertEqual(sec_results[0].assessment_section_id, self.section_id)

    def test_objective_only_attempt_transitions_to_evaluated_and_final(self):
        """
        Verify that an objective-only attempt transitions directly to EVALUATED
        with AttemptResult.status = FINAL in the same transaction.
        """
        obj_items = [self.mixed_items[0], self.mixed_items[1]]  # MCQ + TF only
        obj_paper_id = uuid.uuid4()
        obj_payload = DeliveryPayloadDTO(
            assessment_paper_id=obj_paper_id,
            duration_seconds=1800,
            is_eligible=True,
            eligibility_error=None,
            items=obj_items,
        )
        obj_port = FakeAssessmentPaperPort(obj_payload)

        obj_attempt = start_attempt(
            student_id=self.student_id,
            paper_id=obj_paper_id,
            authorization_context=self.auth_context,
            assessment_port=obj_port,
            now=self.fixed_now,
        )
        obj_items_list = list(obj_attempt.items.order_by("presentation_order"))

        # Answer MCQ correctly
        save_response(
            attempt_id=obj_attempt.id,
            attempt_item_id=obj_items_list[0].id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
            now=self.fixed_now + timedelta(minutes=2),
        )
        # Answer TF correctly
        save_response(
            attempt_id=obj_attempt.id,
            attempt_item_id=obj_items_list[1].id,
            authorization=self.auth_context,
            response_data={"question_type": "TRUE_FALSE", "boolean_response": True},
            now=self.fixed_now + timedelta(minutes=3),
        )

        submit_now = self.fixed_now + timedelta(minutes=10)
        submitted_attempt, result = submit_attempt(
            attempt_id=obj_attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=submit_now,
        )

        # Lifecycle check: objective-only goes IN_PROGRESS -> SUBMITTED -> EVALUATED
        self.assertEqual(submitted_attempt.status, AttemptStatus.EVALUATED)
        self.assertEqual(submitted_attempt.submission_reason, SubmissionReason.MANUAL)
        self.assertEqual(submitted_attempt.submitted_at, submit_now)

        # Result is FINAL and finalized_at is set
        self.assertEqual(result.status, AttemptResultStatus.FINAL)
        self.assertEqual(result.finalized_at, submit_now)
        self.assertEqual(result.total_questions, 2)
        self.assertEqual(result.attempted_questions, 2)
        self.assertEqual(result.correct_questions, 2)
        self.assertEqual(result.pending_evaluation_questions, 0)
        self.assertEqual(result.score, Decimal("3.00"))
        self.assertEqual(result.percentage, Decimal("100.00"))

    # --- TIMING & EXPIRY TESTS ---

    def test_submit_at_or_after_expiry_becomes_timeout_submission(self):
        """
        Verify that when submit_attempt is called at or after expires_at:
        - It processes as a TIMEOUT submission.
        - Does NOT raise AttemptExpired (unlike response mutation).
        - Sets submission_reason = TIMEOUT.
        """
        exact_expiry = self.attempt.expires_at

        # Call submit_attempt at exact expiry
        submitted_attempt, result = submit_attempt(
            attempt_id=self.attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=exact_expiry,
        )

        self.assertEqual(submitted_attempt.status, AttemptStatus.SUBMITTED)
        self.assertEqual(submitted_attempt.submission_reason, SubmissionReason.TIMEOUT)
        self.assertEqual(submitted_attempt.submitted_at, exact_expiry)

    def test_submit_after_expiry_becomes_timeout_submission(self):
        after_expiry = self.attempt.expires_at + timedelta(seconds=120)

        submitted_attempt, result = submit_attempt(
            attempt_id=self.attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=after_expiry,
        )

        self.assertEqual(submitted_attempt.status, AttemptStatus.SUBMITTED)
        self.assertEqual(submitted_attempt.submission_reason, SubmissionReason.TIMEOUT)
        self.assertEqual(submitted_attempt.submitted_at, after_expiry)

    def test_exact_deadline_boundary_behavior(self):
        """
        Boundary verification:
        now == expires_at - 1 microsecond -> MANUAL
        now == expires_at -> TIMEOUT
        """
        just_before = self.attempt.expires_at - timedelta(microseconds=1)
        submitted_attempt, _ = submit_attempt(
            attempt_id=self.attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=just_before,
        )
        self.assertEqual(submitted_attempt.submission_reason, SubmissionReason.MANUAL)

    # --- AUTHORIZATION TESTS ---

    def test_student_cannot_submit_another_students_attempt(self):
        other_student = uuid.uuid4()
        other_auth = AuthorizationContext(actor_id=other_student, is_student=True, is_superadmin=False)

        with self.assertRaises(AttemptAuthorizationError):
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=other_auth,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_superadmin_cannot_submit_as_student(self):
        superadmin_id = uuid.uuid4()
        superadmin_auth = AuthorizationContext(
            actor_id=superadmin_id,
            is_student=False,
            is_superadmin=True,
        )

        with self.assertRaises(AttemptAuthorizationError):
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=superadmin_auth,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_non_student_rejected(self):
        non_student_auth = AuthorizationContext(
            actor_id=self.student_id,
            is_student=False,
            is_superadmin=False,
        )

        with self.assertRaises(AttemptAuthorizationError):
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=non_student_auth,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=5),
            )

    # --- SCORING POLICY TESTS ---

    def test_scoring_policy_omission_fails_explicitly(self):
        with self.assertRaises(ValueError) as cm:
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=self.auth_context,
                scoring_policy=None,  # type: ignore[arg-type]
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=5),
            )
        self.assertIn("ScoringPolicy must be explicitly provided", str(cm.exception))

    def test_all_three_scoring_policies_work_with_submit_attempt(self):
        """
        Verify that Unrestricted, ZeroFloorTotal, and ZeroFloorSection
        policies can all be explicitly injected and work correctly.
        """
        # Answer MCQ incorrectly: choice_1b gives -0.66 penalty
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=self.items[0].id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1b},
            now=self.fixed_now + timedelta(minutes=5),
        )

        # 1. Unrestricted policy retains negative score
        attempt_unres, res_unres = submit_attempt(
            attempt_id=self.attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=self.fixed_now + timedelta(minutes=10),
        )
        self.assertEqual(res_unres.score, Decimal("-0.66"))

        # Create fresh attempt for ZeroFloorTotal
        attempt_zft = start_attempt(
            student_id=self.student_id,
            paper_id=uuid.uuid4(),
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now,
        )
        save_response(
            attempt_id=attempt_zft.id,
            attempt_item_id=attempt_zft.items.order_by("presentation_order").first().id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1b},
            now=self.fixed_now + timedelta(minutes=5),
        )
        _, res_zft = submit_attempt(
            attempt_id=attempt_zft.id,
            authorization=self.auth_context,
            scoring_policy=ZeroFloorTotalScoringPolicy(),
            question_bank_port=self.qb_port,
            now=self.fixed_now + timedelta(minutes=10),
        )
        self.assertEqual(res_zft.score, Decimal("0.00"))

        # Create fresh attempt for ZeroFloorSection
        attempt_zfs = start_attempt(
            student_id=self.student_id,
            paper_id=uuid.uuid4(),
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now,
        )
        save_response(
            attempt_id=attempt_zfs.id,
            attempt_item_id=attempt_zfs.items.order_by("presentation_order").first().id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1b},
            now=self.fixed_now + timedelta(minutes=5),
        )
        _, res_zfs = submit_attempt(
            attempt_id=attempt_zfs.id,
            authorization=self.auth_context,
            scoring_policy=ZeroFloorSectionScoringPolicy(),
            question_bank_port=self.qb_port,
            now=self.fixed_now + timedelta(minutes=10),
        )
        sec_res = AttemptSectionResult.objects.get(attempt_result=res_zfs)
        self.assertEqual(sec_res.score, Decimal("0.00"))

    # --- STATE SAFETY & IDEMPOTENCY TESTS ---

    def test_cannot_submit_already_submitted_attempt(self):
        # First submission succeeds
        submit_attempt(
            attempt_id=self.attempt.id,
            authorization=self.auth_context,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
            now=self.fixed_now + timedelta(minutes=10),
        )

        # Second submission rejected
        with self.assertRaises(InvalidAttemptStateError):
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=self.auth_context,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=11),
            )

        # Cardinality guarantees: exactly 1 AttemptResult and 3 evaluations
        self.assertEqual(AttemptResult.objects.filter(attempt=self.attempt).count(), 1)
        self.assertEqual(AttemptEvaluation.objects.filter(attempt_item__attempt=self.attempt).count(), 3)

    def test_cannot_submit_evaluated_attempt(self):
        self.attempt.status = AttemptStatus.EVALUATED
        self.attempt.submitted_at = self.fixed_now
        self.attempt.save()

        with self.assertRaises(InvalidAttemptStateError):
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=self.auth_context,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=10),
            )

    def test_cannot_submit_cancelled_attempt(self):
        self.attempt.status = AttemptStatus.CANCELLED
        self.attempt.cancelled_at = self.fixed_now
        self.attempt.cancelled_by = self.student_id
        self.attempt.cancellation_reason = "Cancelled by student"
        self.attempt.save()

        with self.assertRaises(InvalidAttemptStateError):
            submit_attempt(
                attempt_id=self.attempt.id,
                authorization=self.auth_context,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=10),
            )

    def test_submit_non_existent_attempt_raises_not_found(self):
        with self.assertRaises(AttemptNotFoundError):
            submit_attempt(
                attempt_id=uuid.uuid4(),
                authorization=self.auth_context,
                scoring_policy=UnrestrictedScoringPolicy(),
                question_bank_port=self.qb_port,
                now=self.fixed_now + timedelta(minutes=10),
            )
