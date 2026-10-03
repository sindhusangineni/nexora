from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from django.test import TestCase

from apps.attempts.application.start_attempt import start_attempt
from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    InvalidDeliveryPayloadError,
    PaperNotEligibleError,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptItemChoice,
    AttemptResponse,
    AttemptResult,
    AttemptSectionResult,
    AttemptStatus,
)
from apps.attempts.ports.assessment import (
    DeliveryPayloadDTO,
    PaperChoiceDTO,
    PaperItemDTO,
    PaperMatchPairDTO,
)


class FakeAssessmentPaperPort:
    def __init__(self, payload: DeliveryPayloadDTO):
        self.payload = payload
        self.calls = []

    def get_paper_delivery_payload(self, paper_id: uuid.UUID, student_id: uuid.UUID) -> DeliveryPayloadDTO:
        self.calls.append((paper_id, student_id))
        return self.payload


class StartAttemptUseCaseTests(TestCase):
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

        self.item_1_id = uuid.uuid4()
        self.q_1_id = uuid.uuid4()
        self.qv_1_id = uuid.uuid4()
        self.choice_1a_id = uuid.uuid4()
        self.choice_1b_id = uuid.uuid4()

        self.item_2_id = uuid.uuid4()
        self.q_2_id = uuid.uuid4()
        self.qv_2_id = uuid.uuid4()
        self.match_l1_id = uuid.uuid4()
        self.match_r1_id = uuid.uuid4()

        self.sample_items = [
            PaperItemDTO(
                paper_item_id=self.item_1_id,
                question_id=self.q_1_id,
                question_version_id=self.qv_1_id,
                question_type="MCQ",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=1,
                allocated_marks=Decimal("2.0000"),
                allocated_penalty=Decimal("0.6666"),
                choices=[
                    PaperChoiceDTO(
                        choice_id=self.choice_1a_id,
                        choice_text="Choice A",
                        presented_position=1,
                    ),
                    PaperChoiceDTO(
                        choice_id=self.choice_1b_id,
                        choice_text="Choice B",
                        presented_position=2,
                    ),
                ],
            ),
            PaperItemDTO(
                paper_item_id=self.item_2_id,
                question_id=self.q_2_id,
                question_version_id=self.qv_2_id,
                question_type="MATCH_FOLLOWING",
                assessment_section_id=self.section_id,
                section_order=1,
                presentation_order=2,
                allocated_marks=Decimal("4.0000"),
                allocated_penalty=Decimal("1.0000"),
                match_pairs=[
                    PaperMatchPairDTO(
                        left_item_id=self.match_l1_id,
                        left_text="Item 1",
                        right_item_id=self.match_r1_id,
                        right_text="Item A",
                    ),
                ],
            ),
        ]

        self.valid_payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=7200,
            is_eligible=True,
            eligibility_error=None,
            items=self.sample_items,
        )
        self.port = FakeAssessmentPaperPort(self.valid_payload)

    def test_successful_first_attempt(self):
        attempt = start_attempt(
            student_id=self.student_id,
            paper_id=self.paper_id,
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now,
        )

        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.student_id, self.student_id)
        self.assertEqual(attempt.assessment_paper_id, self.paper_id)
        self.assertEqual(attempt.attempt_number, 1)
        self.assertEqual(attempt.duration_seconds, 7200)
        self.assertEqual(attempt.started_at, self.fixed_now)
        self.assertEqual(attempt.expires_at, self.fixed_now + timedelta(seconds=7200))
        self.assertEqual(attempt.status, AttemptStatus.IN_PROGRESS)

        # Check AttemptItems
        items = list(AttemptItem.objects.filter(attempt=attempt).order_by("presentation_order"))
        self.assertEqual(len(items), 2)

        item1 = items[0]
        self.assertEqual(item1.paper_item_id, self.item_1_id)
        self.assertEqual(item1.question_id, self.q_1_id)
        self.assertEqual(item1.question_version_id, self.qv_1_id)
        self.assertEqual(item1.assessment_section_id, self.section_id)
        self.assertEqual(item1.presentation_order, 1)
        self.assertEqual(item1.allocated_marks, Decimal("2.0000"))
        self.assertEqual(item1.allocated_penalty, Decimal("0.6666"))

        # Check AttemptItemChoices
        choices = list(AttemptItemChoice.objects.filter(attempt_item=item1).order_by("presented_position"))
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[0].choice_id, self.choice_1a_id)
        self.assertEqual(choices[0].presented_position, 1)
        self.assertEqual(choices[1].choice_id, self.choice_1b_id)
        self.assertEqual(choices[1].presented_position, 2)

        # Check AttemptResponses
        for item in items:
            resp = AttemptResponse.objects.get(attempt_item=item)
            self.assertEqual(resp.answer_state, AnswerState.UNANSWERED)
            self.assertIsNone(resp.boolean_response)
            self.assertIsNone(resp.text_response)
            self.assertIsNone(resp.assertion_reason_response)

        # Verify no evaluation or result models are created
        self.assertEqual(AttemptEvaluation.objects.count(), 0)
        self.assertEqual(AttemptResult.objects.count(), 0)
        self.assertEqual(AttemptSectionResult.objects.count(), 0)

    def test_idempotent_active_attempt(self):
        attempt_1 = start_attempt(
            student_id=self.student_id,
            paper_id=self.paper_id,
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now,
        )

        attempt_count_before = Attempt.objects.count()
        item_count_before = AttemptItem.objects.count()
        choice_count_before = AttemptItemChoice.objects.count()
        response_count_before = AttemptResponse.objects.count()

        # Second call with the same student and paper
        attempt_2 = start_attempt(
            student_id=self.student_id,
            paper_id=self.paper_id,
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now + timedelta(minutes=5),
        )

        self.assertEqual(attempt_1.id, attempt_2.id)
        self.assertEqual(attempt_2.attempt_number, 1)
        self.assertEqual(Attempt.objects.count(), attempt_count_before)
        self.assertEqual(AttemptItem.objects.count(), item_count_before)
        self.assertEqual(AttemptItemChoice.objects.count(), choice_count_before)
        self.assertEqual(AttemptResponse.objects.count(), response_count_before)

    def test_retake_allocates_next_attempt_number(self):
        first_attempt = start_attempt(
            student_id=self.student_id,
            paper_id=self.paper_id,
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now,
        )
        self.assertEqual(first_attempt.attempt_number, 1)

        # Simulate first attempt submission so it is no longer IN_PROGRESS
        first_attempt.status = AttemptStatus.SUBMITTED
        first_attempt.submitted_at = self.fixed_now + timedelta(minutes=30)
        first_attempt.save()

        # Starting again creates attempt_number = 2
        second_attempt = start_attempt(
            student_id=self.student_id,
            paper_id=self.paper_id,
            authorization_context=self.auth_context,
            assessment_port=self.port,
            now=self.fixed_now + timedelta(days=1),
        )

        self.assertNotEqual(first_attempt.id, second_attempt.id)
        self.assertEqual(second_attempt.attempt_number, 2)
        self.assertEqual(Attempt.objects.filter(student_id=self.student_id, assessment_paper_id=self.paper_id).count(), 2)

    def test_ineligible_paper_rejected(self):
        ineligible_payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=False,
            eligibility_error="Assessment window has expired.",
            items=self.sample_items,
        )
        port = FakeAssessmentPaperPort(ineligible_payload)

        with self.assertRaises(PaperNotEligibleError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("Assessment window has expired.", str(cm.exception))
        self.assertEqual(Attempt.objects.count(), 0)

    def test_invalid_duration_rejected(self):
        payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=0,
            is_eligible=True,
            eligibility_error=None,
            items=self.sample_items,
        )
        port = FakeAssessmentPaperPort(payload)

        with self.assertRaises(InvalidDeliveryPayloadError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("duration must be strictly positive", str(cm.exception))
        self.assertEqual(Attempt.objects.count(), 0)

    def test_empty_items_rejected(self):
        payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=[],
        )
        port = FakeAssessmentPaperPort(payload)

        with self.assertRaises(InvalidDeliveryPayloadError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("at least one item", str(cm.exception))
        self.assertEqual(Attempt.objects.count(), 0)

    def test_duplicate_paper_item_id_rejected_and_rolled_back(self):
        dup_item = PaperItemDTO(
            paper_item_id=self.item_1_id,  # duplicate ID
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            question_type="MCQ",
            assessment_section_id=self.section_id,
            section_order=1,
            presentation_order=3,
            allocated_marks=Decimal("1.0000"),
            allocated_penalty=Decimal("0.0000"),
        )
        payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=self.sample_items + [dup_item],
        )
        port = FakeAssessmentPaperPort(payload)

        with self.assertRaises(InvalidDeliveryPayloadError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("Duplicate paper_item_id", str(cm.exception))
        self.assertEqual(Attempt.objects.count(), 0)

    def test_duplicate_presentation_order_rejected(self):
        dup_order_item = PaperItemDTO(
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            question_type="MCQ",
            assessment_section_id=self.section_id,
            section_order=1,
            presentation_order=1,  # duplicate order
            allocated_marks=Decimal("1.0000"),
            allocated_penalty=Decimal("0.0000"),
        )
        payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=self.sample_items + [dup_order_item],
        )
        port = FakeAssessmentPaperPort(payload)

        with self.assertRaises(InvalidDeliveryPayloadError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("Duplicate presentation_order", str(cm.exception))
        self.assertEqual(Attempt.objects.count(), 0)

    def test_negative_allocated_marks_rejected(self):
        bad_item = PaperItemDTO(
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            question_type="MCQ",
            assessment_section_id=self.section_id,
            section_order=1,
            presentation_order=3,
            allocated_marks=Decimal("0.0000"),  # non-positive
            allocated_penalty=Decimal("0.0000"),
        )
        payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=[bad_item],
        )
        port = FakeAssessmentPaperPort(payload)

        with self.assertRaises(InvalidDeliveryPayloadError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("allocated_marks must be strictly positive", str(cm.exception))

    def test_duplicate_choice_positions_rejected(self):
        bad_choice_item = PaperItemDTO(
            paper_item_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            question_version_id=uuid.uuid4(),
            question_type="MCQ",
            assessment_section_id=self.section_id,
            section_order=1,
            presentation_order=1,
            allocated_marks=Decimal("1.0000"),
            allocated_penalty=Decimal("0.0000"),
            choices=[
                PaperChoiceDTO(choice_id=uuid.uuid4(), choice_text="A", presented_position=1),
                PaperChoiceDTO(choice_id=uuid.uuid4(), choice_text="B", presented_position=1),  # dup pos
            ],
        )
        payload = DeliveryPayloadDTO(
            assessment_paper_id=self.paper_id,
            duration_seconds=3600,
            is_eligible=True,
            eligibility_error=None,
            items=[bad_choice_item],
        )
        port = FakeAssessmentPaperPort(payload)

        with self.assertRaises(InvalidDeliveryPayloadError) as cm:
            start_attempt(
                student_id=self.student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,
                assessment_port=port,
                now=self.fixed_now,
            )
        self.assertIn("Duplicate choice presented_position", str(cm.exception))

    def test_authorization_enforced(self):
        other_student_id = uuid.uuid4()
        with self.assertRaises(AttemptAuthorizationError):
            start_attempt(
                student_id=other_student_id,
                paper_id=self.paper_id,
                authorization_context=self.auth_context,  # auth context has self.student_id
                assessment_port=self.port,
                now=self.fixed_now,
            )
