from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from django.test import TestCase

from apps.attempts.application.clear_response import clear_response
from apps.attempts.application.save_response import save_response
from apps.attempts.application.start_attempt import start_attempt
from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptExpired,
    AttemptNotFoundError,
    InvalidAttemptStateError,
    InvalidResponseError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptItemChoice,
    AttemptResponse,
    AttemptResponseChoice,
    AttemptResponseMatch,
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
from apps.attempts.services.response_validation import validate_descriptive_response
from apps.attempts.services.scoring import (
    ScoringPolicy,
    UnrestrictedScoringPolicy,
    ZeroFloorSectionScoringPolicy,
    ZeroFloorTotalScoringPolicy,
)
from apps.attempts.services.timeout_submission import execute_timeout_submission


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


class ResponseMutationTests(TestCase):
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

        # Multiple Select Item (Item 2)
        self.ms_item_id = uuid.uuid4()
        self.ms_qv_id = uuid.uuid4()
        self.choice_2a = uuid.uuid4()
        self.choice_2b = uuid.uuid4()
        self.choice_2c = uuid.uuid4()

        # True/False Item (Item 3)
        self.tf_item_id = uuid.uuid4()
        self.tf_qv_id = uuid.uuid4()

        # Assertion/Reason Item (Item 4)
        self.ar_item_id = uuid.uuid4()
        self.ar_qv_id = uuid.uuid4()

        # Match Following Item (Item 5)
        self.mf_item_id = uuid.uuid4()
        self.mf_qv_id = uuid.uuid4()
        self.l1 = uuid.uuid4()
        self.l2 = uuid.uuid4()
        self.r1 = uuid.uuid4()
        self.r2 = uuid.uuid4()

        # Descriptive Item (Item 6)
        self.desc_item_id = uuid.uuid4()
        self.desc_qv_id = uuid.uuid4()

        items = [
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
                paper_item_id=self.ms_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.ms_qv_id,
                question_type="MULTIPLE_SELECT",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=2,
                allocated_marks=Decimal("4.0000"),
                allocated_penalty=Decimal("1.0000"),
                choices=[
                    PaperChoiceDTO(choice_id=self.choice_2a, choice_text="A", presented_position=1),
                    PaperChoiceDTO(choice_id=self.choice_2b, choice_text="B", presented_position=2),
                    PaperChoiceDTO(choice_id=self.choice_2c, choice_text="C", presented_position=3),
                ],
            ),
            PaperItemDTO(
                paper_item_id=self.tf_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.tf_qv_id,
                question_type="TRUE_FALSE",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=3,
                allocated_marks=Decimal("1.0000"),
                allocated_penalty=Decimal("0.3300"),
            ),
            PaperItemDTO(
                paper_item_id=self.ar_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.ar_qv_id,
                question_type="ASSERTION_REASON",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=4,
                allocated_marks=Decimal("2.0000"),
                allocated_penalty=Decimal("0.6600"),
            ),
            PaperItemDTO(
                paper_item_id=self.mf_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.mf_qv_id,
                question_type="MATCH_FOLLOWING",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=5,
                allocated_marks=Decimal("4.0000"),
                allocated_penalty=Decimal("1.0000"),
                match_pairs=[
                    PaperMatchPairDTO(left_item_id=self.l1, left_text="L1", right_item_id=self.r1, right_text="R1"),
                    PaperMatchPairDTO(left_item_id=self.l2, left_text="L2", right_item_id=self.r2, right_text="R2"),
                ],
            ),
            PaperItemDTO(
                paper_item_id=self.desc_item_id,
                question_id=uuid.uuid4(),
                question_version_id=self.desc_qv_id,
                question_type="DESCRIPTIVE",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=6,
                allocated_marks=Decimal("10.0000"),
                allocated_penalty=Decimal("0.0000"),
            ),
        ]

        self.payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=items,
        )
        self.port = FakeAssessmentPaperPort(self.payload)

        # Answer keys for timeout evaluation
        self.qb_keys = {
            self.mcq_qv_id: ObjectiveAnswerKeyDTO(
                question_version_id=self.mcq_qv_id,
                question_type="MCQ",
                correct_choice_ids={self.choice_1a},
                correct_boolean=None,
                correct_assertion_reason=None,
                correct_match_pairs={},
            ),
            self.ms_qv_id: ObjectiveAnswerKeyDTO(
                question_version_id=self.ms_qv_id,
                question_type="MULTIPLE_SELECT",
                correct_choice_ids={self.choice_2a, self.choice_2b},
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
            self.ar_qv_id: ObjectiveAnswerKeyDTO(
                question_version_id=self.ar_qv_id,
                question_type="ASSERTION_REASON",
                correct_choice_ids=set(),
                correct_boolean=None,
                correct_assertion_reason="BOTH_TRUE_REASON_CORRECT",
                correct_match_pairs={},
            ),
            self.mf_qv_id: ObjectiveAnswerKeyDTO(
                question_version_id=self.mf_qv_id,
                question_type="MATCH_FOLLOWING",
                correct_choice_ids=set(),
                correct_boolean=None,
                correct_assertion_reason=None,
                correct_match_pairs={self.l1: self.r1, self.l2: self.r2},
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

    # --- SAVE RESPONSE TESTS ---

    def test_mcq_valid_answer(self):
        item = self.items[0]
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp.answer_state, AnswerState.ANSWERED)
        choices = list(resp.choices.all())
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0].choice_id, self.choice_1a)

    def test_mcq_invalid_choice_rejected(self):
        item = self.items[0]
        foreign_choice_id = uuid.uuid4()
        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "MCQ", "choice_id": foreign_choice_id},
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_multiple_select_valid_selections(self):
        item = self.items[1]
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MULTIPLE_SELECT", "selected_choice_ids": [self.choice_2a, self.choice_2c]},
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp.answer_state, AnswerState.ANSWERED)
        selected_ids = set(resp.choices.values_list("choice_id", flat=True))
        self.assertEqual(selected_ids, {self.choice_2a, self.choice_2c})

    def test_multiple_select_empty_selection_rejected(self):
        item = self.items[1]
        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "MULTIPLE_SELECT", "selected_choice_ids": []},
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_multiple_select_foreign_choice_rejected(self):
        item = self.items[1]
        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "MULTIPLE_SELECT", "selected_choice_ids": [self.choice_2a, uuid.uuid4()]},
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_true_false_responses(self):
        item = self.items[2]
        resp_true = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "TRUE_FALSE", "boolean_response": True},
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp_true.boolean_response, True)
        self.assertEqual(resp_true.answer_state, AnswerState.ANSWERED)

        resp_false = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "TRUE_FALSE", "boolean_response": False},
            now=self.fixed_now + timedelta(minutes=6),
        )
        self.assertEqual(resp_false.boolean_response, False)

    def test_assertion_reason_valid_and_invalid(self):
        item = self.items[3]
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "ASSERTION_REASON", "assertion_reason_response": "BOTH_TRUE_REASON_CORRECT"},
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp.assertion_reason_response, "BOTH_TRUE_REASON_CORRECT")

        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "ASSERTION_REASON", "assertion_reason_response": "INVALID_VALUE"},
                now=self.fixed_now + timedelta(minutes=6),
            )

    def test_match_following_complete_valid_mapping(self):
        item = self.items[4]
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={
                "question_type": "MATCH_FOLLOWING",
                "match_pairs": [
                    {"left_item_id": self.l1, "right_item_id": self.r2},
                    {"left_item_id": self.l2, "right_item_id": self.r1},
                ],
                "expected_left_ids": {self.l1, self.l2},
                "expected_right_ids": {self.r1, self.r2},
            },
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp.answer_state, AnswerState.ANSWERED)
        matches = {m.left_item_id: m.right_item_id for m in resp.matches.all()}
        self.assertEqual(matches, {self.l1: self.r2, self.l2: self.r1})

    def test_match_following_incomplete_mapping_rejected(self):
        item = self.items[4]
        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={
                    "question_type": "MATCH_FOLLOWING",
                    "match_pairs": [{"left_item_id": self.l1, "right_item_id": self.r1}],
                    "expected_left_ids": {self.l1, self.l2},
                },
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_match_following_duplicate_right_item_rejected(self):
        item = self.items[4]
        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={
                    "question_type": "MATCH_FOLLOWING",
                    "match_pairs": [
                        {"left_item_id": self.l1, "right_item_id": self.r1},
                        {"left_item_id": self.l2, "right_item_id": self.r1},  # duplicate r1
                    ],
                },
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_descriptive_valid_and_empty_rejected(self):
        item = self.items[5]
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "DESCRIPTIVE", "text_response": "This is a detailed analysis."},
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp.text_response, "This is a detailed analysis.")

        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "DESCRIPTIVE", "text_response": "   "},
                now=self.fixed_now + timedelta(minutes=6),
            )

    def test_stale_child_selections_replaced_cleanly(self):
        item = self.items[1]  # Multiple select
        # First save with choice 2a and 2b
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MULTIPLE_SELECT", "selected_choice_ids": [self.choice_2a, self.choice_2b]},
            now=self.fixed_now + timedelta(minutes=5),
        )

        # Overwrite with choice 2c only
        resp2 = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MULTIPLE_SELECT", "selected_choice_ids": [self.choice_2c]},
            now=self.fixed_now + timedelta(minutes=6),
        )

        selected = set(resp2.choices.values_list("choice_id", flat=True))
        self.assertEqual(selected, {self.choice_2c})
        self.assertEqual(AttemptResponse.objects.filter(attempt_item=item).count(), 1)

    def test_target_attempt_item_ownership_enforced(self):
        # Create a second attempt for another student/paper
        other_student = uuid.uuid4()
        other_auth = AuthorizationContext(actor_id=other_student, is_student=True, is_superadmin=False)
        other_attempt = start_attempt(
            student_id=other_student,
            paper_id=self.paper_id,
            authorization_context=other_auth,
            assessment_port=self.port,
            now=self.fixed_now,
        )
        other_item = other_attempt.items.first()

        # Attempt to mutate other_item on self.attempt must fail with AttemptNotFoundError
        with self.assertRaises(AttemptNotFoundError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=other_item.id,
                authorization=self.auth_context,
                response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
                now=self.fixed_now + timedelta(minutes=5),
            )

    # --- CLEAR RESPONSE TESTS ---

    def test_clear_response_mcq(self):
        item = self.items[0]
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
            now=self.fixed_now + timedelta(minutes=5),
        )

        cleared = clear_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            now=self.fixed_now + timedelta(minutes=6),
        )
        self.assertEqual(cleared.answer_state, AnswerState.UNANSWERED)
        self.assertEqual(cleared.choices.count(), 0)
        self.assertIsNone(cleared.boolean_response)

    def test_clear_response_preserves_response_row(self):
        item = self.items[5]  # Descriptive
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "DESCRIPTIVE", "text_response": "Some answer"},
            now=self.fixed_now + timedelta(minutes=5),
        )
        initial_id = AttemptResponse.objects.get(attempt_item=item).id

        cleared = clear_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            now=self.fixed_now + timedelta(minutes=6),
        )
        self.assertEqual(cleared.id, initial_id)
        self.assertEqual(cleared.answer_state, AnswerState.UNANSWERED)
        self.assertIsNone(cleared.text_response)

    # --- OWNERSHIP & LIFECYCLE TESTS ---

    def test_student_cannot_mutate_another_students_attempt(self):
        other_student = uuid.uuid4()
        other_auth = AuthorizationContext(actor_id=other_student, is_student=True, is_superadmin=False)
        item = self.items[0]

        with self.assertRaises(AttemptAuthorizationError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=other_auth,
                response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
                now=self.fixed_now + timedelta(minutes=5),
            )

    def test_cannot_mutate_submitted_evaluated_or_cancelled_attempt(self):
        item = self.items[0]

        for invalid_status in (AttemptStatus.SUBMITTED, AttemptStatus.EVALUATED, AttemptStatus.CANCELLED):
            self.attempt.status = invalid_status
            if invalid_status == AttemptStatus.CANCELLED:
                self.attempt.cancelled_at = self.fixed_now
                self.attempt.cancelled_by = self.student_id
                self.attempt.cancellation_reason = "Testing cancellation"
            else:
                self.attempt.submitted_at = self.fixed_now
                self.attempt.submission_reason = SubmissionReason.MANUAL
            self.attempt.save()

            with self.assertRaises(InvalidAttemptStateError):
                save_response(
                    attempt_id=self.attempt.id,
                    attempt_item_id=item.id,
                    authorization=self.auth_context,
                    response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
                    now=self.fixed_now + timedelta(minutes=5),
                )

            with self.assertRaises(InvalidAttemptStateError):
                clear_response(
                    attempt_id=self.attempt.id,
                    attempt_item_id=item.id,
                    authorization=self.auth_context,
                    now=self.fixed_now + timedelta(minutes=5),
                )

    # --- TIMING & DURABLE TIMEOUT SUBMISSION TESTS ---

    def test_save_response_before_expiry_succeeds(self):
        item = self.items[0]
        # expires_at is fixed_now + 3600 seconds
        before_expiry = self.attempt.expires_at - timedelta(seconds=1)
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
            now=before_expiry,
        )
        self.assertEqual(resp.answer_state, AnswerState.ANSWERED)
        self.assertEqual(Attempt.objects.get(id=self.attempt.id).status, AttemptStatus.IN_PROGRESS)

    def test_critical_timeout_rollback_safety_save_response(self):
        """
        MANDATORY ROLLBACK SAFETY TEST:
        Proves that raising AttemptExpired post-commit does NOT roll back the timeout submission.
        """
        item = self.items[0]
        exact_expiry = self.attempt.expires_at

        # Attempt to save response at exact expiry
        with self.assertRaises(AttemptExpired) as cm:
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
                question_bank_port=self.qb_port,
                scoring_policy=UnrestrictedScoringPolicy(),
                now=exact_expiry,
            )

        self.assertEqual(cm.exception.status_code, 409)
        self.assertEqual(cm.exception.code, "ATTEMPT_EXPIRED")

        # Query database afresh to verify timeout submission committed durably
        reloaded_attempt = Attempt.objects.get(id=self.attempt.id)
        # Contains descriptive question (item 6), so should transition to SUBMITTED + PENDING result
        self.assertEqual(reloaded_attempt.status, AttemptStatus.SUBMITTED)
        self.assertEqual(reloaded_attempt.submission_reason, SubmissionReason.TIMEOUT)
        self.assertEqual(reloaded_attempt.submitted_at, exact_expiry)

        # Proposed answer was REJECTED: response remains UNANSWERED with 0 choices
        reloaded_resp = AttemptResponse.objects.get(attempt_item=item)
        self.assertEqual(reloaded_resp.answer_state, AnswerState.UNANSWERED)
        self.assertEqual(reloaded_resp.choices.count(), 0)

        # Evaluations exist for all items
        self.assertEqual(AttemptEvaluation.objects.filter(attempt_item__attempt=reloaded_attempt).count(), 6)

        # Result exists with status PENDING (since item 6 is descriptive)
        result = AttemptResult.objects.get(attempt=reloaded_attempt)
        self.assertEqual(result.status, AttemptResultStatus.PENDING)
        self.assertIsNone(result.finalized_at)

        # Section result exists
        self.assertEqual(AttemptSectionResult.objects.filter(attempt_result=result).count(), 1)

    def test_critical_timeout_rollback_safety_clear_response(self):
        """
        MANDATORY ROLLBACK SAFETY TEST FOR CLEAR_RESPONSE:
        Proves that raising AttemptExpired on clear_response does NOT roll back timeout submission
        and preserves existing student answers.
        """
        item = self.items[0]
        # Student answered before expiry
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
            now=self.fixed_now + timedelta(minutes=10),
        )

        after_expiry = self.attempt.expires_at + timedelta(seconds=10)

        with self.assertRaises(AttemptExpired) as cm:
            clear_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                question_bank_port=self.qb_port,
                scoring_policy=UnrestrictedScoringPolicy(),
                now=after_expiry,
            )

        self.assertEqual(cm.exception.status_code, 409)

        # Verify durable commit in database
        reloaded_attempt = Attempt.objects.get(id=self.attempt.id)
        self.assertEqual(reloaded_attempt.status, AttemptStatus.SUBMITTED)
        self.assertEqual(reloaded_attempt.submission_reason, SubmissionReason.TIMEOUT)

        # Existing answer was preserved! Not cleared!
        reloaded_resp = AttemptResponse.objects.get(attempt_item=item)
        self.assertEqual(reloaded_resp.answer_state, AnswerState.ANSWERED)
        self.assertEqual(reloaded_resp.choices.count(), 1)
        self.assertEqual(reloaded_resp.choices.first().choice_id, self.choice_1a)

    # --- SCORING POLICY TESTS ---

    def test_timeout_submission_omission_fails_explicitly(self):
        """
        Verify that:
        1. Calling execute_timeout_submission with scoring_policy=None raises ValueError.
        2. Calling expired save_response without scoring_policy raises ValueError.
        3. Calling expired clear_response without scoring_policy raises ValueError.
        Proves no default scoring policy is silently selected.
        """
        item = self.items[0]
        exact_expiry = self.attempt.expires_at

        # 1. Direct timeout submission omission
        with self.assertRaises(ValueError) as cm1:
            execute_timeout_submission(
                attempt=self.attempt,
                now=exact_expiry,
                scoring_policy=None,  # type: ignore[arg-type]
                question_bank_port=self.qb_port,
            )
        self.assertIn("ScoringPolicy must be explicitly provided", str(cm1.exception))

        # 2. save_response on expired attempt without scoring_policy
        with self.assertRaises(ValueError) as cm2:
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "MCQ", "choice_id": self.choice_1a},
                question_bank_port=self.qb_port,
                scoring_policy=None,
                now=exact_expiry,
            )
        self.assertIn("ScoringPolicy must be explicitly provided", str(cm2.exception))

        # 3. clear_response on expired attempt without scoring_policy
        with self.assertRaises(ValueError) as cm3:
            clear_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                question_bank_port=self.qb_port,
                scoring_policy=None,
                now=exact_expiry,
            )
        self.assertIn("ScoringPolicy must be explicitly provided", str(cm3.exception))

    def test_timeout_submission_with_explicit_unrestricted_scoring_policy(self):
        """
        Verify that an explicitly supplied UnrestrictedScoringPolicy works
        and preserves negative scores.
        """
        # Answer item 0 (MCQ) incorrectly: choice_1b instead of choice_1a
        item_mcq = self.items[0]
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item_mcq.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1b},
            now=self.fixed_now + timedelta(minutes=5),
        )

        # Trigger timeout submission with UnrestrictedScoringPolicy
        # Allocated marks: item 0 has marks 2.0, penalty 0.66.
        # Wrong answer = -0.66 deduction.
        # Other items are UNANSWERED (0 marks) or DESCRIPTIVE (0 marks).
        # Raw score = -0.66, which under UnrestrictedScoringPolicy yields negative score.
        attempt, result = execute_timeout_submission(
            attempt=self.attempt,
            now=self.attempt.expires_at,
            scoring_policy=UnrestrictedScoringPolicy(),
            question_bank_port=self.qb_port,
        )

        self.assertEqual(result.score, Decimal("-0.66"))
        self.assertTrue(result.percentage < Decimal("0.00"))

    def test_timeout_submission_with_explicit_zero_floor_total_scoring_policy(self):
        """
        Verify that an explicitly supplied ZeroFloorTotalScoringPolicy works
        and floors negative total scores at zero.
        """
        # Answer item 0 (MCQ) incorrectly
        item_mcq = self.items[0]
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item_mcq.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1b},
            now=self.fixed_now + timedelta(minutes=5),
        )

        attempt, result = execute_timeout_submission(
            attempt=self.attempt,
            now=self.attempt.expires_at,
            scoring_policy=ZeroFloorTotalScoringPolicy(),
            question_bank_port=self.qb_port,
        )

        self.assertEqual(result.raw_score, Decimal("-0.6600"))
        self.assertEqual(result.score, Decimal("0.00"))
        self.assertEqual(result.percentage, Decimal("0.00"))

    def test_timeout_submission_with_explicit_zero_floor_section_scoring_policy(self):
        """
        Verify that an explicitly supplied ZeroFloorSectionScoringPolicy works
        and floors negative section scores at zero.
        """
        # Answer item 0 (MCQ) incorrectly
        item_mcq = self.items[0]
        save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item_mcq.id,
            authorization=self.auth_context,
            response_data={"question_type": "MCQ", "choice_id": self.choice_1b},
            now=self.fixed_now + timedelta(minutes=5),
        )

        attempt, result = execute_timeout_submission(
            attempt=self.attempt,
            now=self.attempt.expires_at,
            scoring_policy=ZeroFloorSectionScoringPolicy(),
            question_bank_port=self.qb_port,
        )

        section_result = AttemptSectionResult.objects.get(attempt_result=result)
        self.assertEqual(section_result.score, Decimal("0.00"))

    def test_all_three_scoring_policies_independently_testable(self):
        """
        Verify that all three ScoringPolicy implementations exist, conform to the interface,
        and are independently testable without any one being privileged as default.
        """
        raw_neg = Decimal("-5.50")
        raw_pos = Decimal("15.00")
        max_marks = Decimal("20.00")

        # 1. Unrestricted
        unrestricted = UnrestrictedScoringPolicy()
        score_neg, pct_neg = unrestricted.calculate_score(raw_neg, max_marks)
        self.assertEqual(score_neg, Decimal("-5.50"))
        self.assertEqual(pct_neg, Decimal("-27.50"))

        score_pos, pct_pos = unrestricted.calculate_score(raw_pos, max_marks)
        self.assertEqual(score_pos, Decimal("15.00"))
        self.assertEqual(pct_pos, Decimal("75.00"))

        # 2. Zero Floor Total
        zero_total = ZeroFloorTotalScoringPolicy()
        score_neg, pct_neg = zero_total.calculate_score(raw_neg, max_marks)
        self.assertEqual(score_neg, Decimal("0.00"))
        self.assertEqual(pct_neg, Decimal("0.00"))

        score_pos, pct_pos = zero_total.calculate_score(raw_pos, max_marks)
        self.assertEqual(score_pos, Decimal("15.00"))
        self.assertEqual(pct_pos, Decimal("75.00"))

        # 3. Zero Floor Section
        zero_sec = ZeroFloorSectionScoringPolicy()
        score_neg, pct_neg = zero_sec.calculate_score(raw_neg, max_marks)
        self.assertEqual(score_neg, Decimal("0.00"))
        self.assertEqual(pct_neg, Decimal("0.00"))

        # Zero max marks edge case
        for policy in (unrestricted, zero_total, zero_sec):
            s, p = policy.calculate_score(Decimal("0.00"), Decimal("0.00"))
            self.assertEqual(s, Decimal("0.00"))
            self.assertEqual(p, Decimal("0.00"))

    # --- DESCRIPTIVE RESPONSE VALIDATION TESTS ---

    def test_descriptive_validation_no_implicit_5000_limit(self):
        """
        Verify that:
        1. Non-empty string is valid.
        2. String longer than 5000 chars (e.g. 6000 chars) is valid by default without any implicit 5000 limit.
        3. Empty and whitespace-only strings are rejected.
        4. Explicit caller-provided max_length bound is enforced without hardcoding 5000.
        """
        item = self.items[5]  # Descriptive item

        # Long text (6000 characters) - previously would fail on 5000 limit
        long_text = "A" * 6000
        resp = save_response(
            attempt_id=self.attempt.id,
            attempt_item_id=item.id,
            authorization=self.auth_context,
            response_data={"question_type": "DESCRIPTIVE", "text_response": long_text},
            now=self.fixed_now + timedelta(minutes=5),
        )
        self.assertEqual(resp.text_response, long_text)
        self.assertEqual(len(resp.text_response), 6000)

        # Empty string rejected
        with self.assertRaises(InvalidResponseError):
            validate_descriptive_response("")

        # Whitespace-only rejected
        with self.assertRaises(InvalidResponseError):
            validate_descriptive_response("   \t\n  ")

        # Non-string rejected
        with self.assertRaises(InvalidResponseError):
            validate_descriptive_response(12345)

        # Caller-specified bound mechanism: respects explicitly supplied max_length
        bounded_text = validate_descriptive_response("Hello World", max_length=20)
        self.assertEqual(bounded_text, "Hello World")

        with self.assertRaises(InvalidResponseError):
            validate_descriptive_response("Hello World", max_length=5)

        # save_response with caller-provided max_length
        with self.assertRaises(InvalidResponseError):
            save_response(
                attempt_id=self.attempt.id,
                attempt_item_id=item.id,
                authorization=self.auth_context,
                response_data={"question_type": "DESCRIPTIVE", "text_response": "Exceeds bound", "max_length": 5},
                now=self.fixed_now + timedelta(minutes=6),
            )
