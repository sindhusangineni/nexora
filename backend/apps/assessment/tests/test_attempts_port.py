import uuid
from decimal import Decimal
import pytest

from apps.assessment.adapters.attempts import AssessmentPaperDeliveryAdapter
from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentSection,
    PaperStatus,
)
from apps.attempts.ports.assessment import (
    AssessmentPaperPort,
    DeliveryPayloadDTO,
)


@pytest.mark.django_db
class TestAttemptsAssessmentPaperPortAdapter:
    def test_adapter_satisfies_protocol(self):
        adapter = AssessmentPaperDeliveryAdapter()
        assert hasattr(adapter, "get_paper_delivery_payload")
        assert callable(adapter.get_paper_delivery_payload)

    def test_nonexistent_paper_returns_ineligible_payload(self):
        adapter = AssessmentPaperDeliveryAdapter()
        paper_id = uuid.uuid4()
        student_id = uuid.uuid4()

        payload = adapter.get_paper_delivery_payload(paper_id, student_id)
        assert isinstance(payload, DeliveryPayloadDTO)
        assert payload.assessment_paper_id == paper_id
        assert payload.is_eligible is False
        assert payload.eligibility_error == "Assessment paper not found."
        assert payload.items == []

    def test_existing_paper_returns_complete_delivery_payload(self):
        assessment = Assessment.objects.create(
            title="Attempts Port Integration Assessment",
            duration_seconds=3600,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.66"),
        )
        sec = AssessmentSection.objects.create(
            assessment=assessment,
            title="General Section",
            position=1,
        )
        paper = AssessmentPaper.objects.create(
            assessment=assessment,
            status=PaperStatus.GENERATED,
            duration_seconds=assessment.duration_seconds,
            marks_per_question=assessment.marks_per_question,
            penalty_per_question=assessment.penalty_per_question,
        )

        q1_id, v1_id = uuid.uuid4(), uuid.uuid4()
        q2_id, v2_id = uuid.uuid4(), uuid.uuid4()

        item1 = AssessmentPaperItem.objects.create(
            paper=paper,
            question_id=q1_id,
            question_version_id=v1_id,
            assessment_section=sec,
            presentation_order=1,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.66"),
        )
        item2 = AssessmentPaperItem.objects.create(
            paper=paper,
            question_id=q2_id,
            question_version_id=v2_id,
            assessment_section=None,
            presentation_order=2,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.66"),
        )

        adapter = AssessmentPaperDeliveryAdapter()
        student_id = uuid.uuid4()
        payload = adapter.get_paper_delivery_payload(paper.id, student_id)

        assert isinstance(payload, DeliveryPayloadDTO)
        assert payload.assessment_paper_id == paper.id
        assert payload.duration_seconds == 3600
        assert payload.is_eligible is True
        assert payload.eligibility_error is None
        assert len(payload.items) == 2

        it1 = payload.items[0]
        assert it1.paper_item_id == item1.id
        assert it1.question_id == q1_id
        assert it1.question_version_id == v1_id
        assert it1.assessment_section_id == sec.id
        assert it1.section_order == 1
        assert it1.presentation_order == 1
        assert it1.allocated_marks == Decimal("2.00")
        assert it1.allocated_penalty == Decimal("0.66")

        it2 = payload.items[1]
        assert it2.paper_item_id == item2.id
        assert it2.question_id == q2_id
        assert it2.question_version_id == v2_id
        assert it2.assessment_section_id is None
        assert it2.section_order == 0
        assert it2.presentation_order == 2
