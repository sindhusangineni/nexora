import uuid
from decimal import Decimal
import pytest

from apps.assessment.application.generate_paper import generate_paper
from apps.assessment.exceptions import (
    AssessmentEmptyError,
    AssessmentNotFoundError,
    AssessmentNotPublishedError,
    AssessmentPaperImmutableError,
    InsufficientQuestionsError,
)
from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentSection,
    AssessmentStatus,
    PaperStatus,
    QuestionType,
    ScopeType,
    SelectionRule,
)
from apps.assessment.ports.question_bank import (
    QuestionBankCandidatePort,
    QuestionCandidateDTO,
)


class FakeCandidatePort(QuestionBankCandidatePort):
    def __init__(self, candidates_by_scope: dict[tuple[str, uuid.UUID], list[QuestionCandidateDTO]]):
        self.candidates_by_scope = candidates_by_scope

    def get_published_candidates(
        self,
        scope_type: str,
        scope_id: uuid.UUID,
        question_type: str | None = None,
        difficulty: str | None = None,
    ) -> list[QuestionCandidateDTO]:
        cands = self.candidates_by_scope.get((scope_type.upper(), scope_id), [])
        if question_type:
            cands = [c for c in cands if c.question_type == question_type]
        if difficulty:
            cands = [c for c in cands if c.difficulty == difficulty]
        return cands


@pytest.mark.django_db
class TestPaperGeneration:
    def test_generate_paper_nonexistent_assessment_raises_404(self):
        port = FakeCandidatePort({})
        with pytest.raises(AssessmentNotFoundError):
            generate_paper(uuid.uuid4(), port)

    def test_generate_paper_draft_assessment_rejected(self):
        assessment = Assessment.objects.create(title="Draft Assessment")
        rule_scope = uuid.uuid4()
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=rule_scope,
            question_count=5,
            position=1,
        )
        port = FakeCandidatePort({})
        with pytest.raises(AssessmentNotPublishedError):
            generate_paper(assessment.id, port)

    def test_generate_paper_archived_assessment_rejected(self):
        assessment = Assessment.objects.create(title="To Be Archived")
        rule_scope = uuid.uuid4()
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=rule_scope,
            question_count=5,
            position=1,
        )
        assessment.publish()
        assessment.archive()

        port = FakeCandidatePort({})
        with pytest.raises(AssessmentNotPublishedError):
            generate_paper(assessment.id, port)

    def test_generate_paper_empty_rules_rejected(self):
        assessment = Assessment.objects.create(title="No Rules Assessment")
        assessment.status = AssessmentStatus.PUBLISHED
        assessment.save(update_fields=["status"])

        port = FakeCandidatePort({})
        with pytest.raises(AssessmentEmptyError):
            generate_paper(assessment.id, port)

    def test_successful_paper_generation_single_rule(self):
        assessment = Assessment.objects.create(
            title="Single Rule Mock",
            duration_seconds=5400,
            marks_per_question=Decimal("2.50"),
            penalty_per_question=Decimal("0.83"),
        )
        topic_id = uuid.uuid4()
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=topic_id,
            question_count=3,
            position=1,
        )
        assessment.publish()

        q1_id, v1_id = uuid.uuid4(), uuid.uuid4()
        q2_id, v2_id = uuid.uuid4(), uuid.uuid4()
        q3_id, v3_id = uuid.uuid4(), uuid.uuid4()

        port = FakeCandidatePort({
            ("TOPIC", topic_id): [
                QuestionCandidateDTO(q1_id, v1_id, "MCQ", "EASY"),
                QuestionCandidateDTO(q2_id, v2_id, "MCQ", "MEDIUM"),
                QuestionCandidateDTO(q3_id, v3_id, "MCQ", "HARD"),
            ]
        })

        paper = generate_paper(assessment.id, port)
        assert paper.id is not None
        assert paper.status == PaperStatus.GENERATED
        assert paper.duration_seconds == 5400
        assert paper.marks_per_question == Decimal("2.50")
        assert paper.penalty_per_question == Decimal("0.83")

        items = list(paper.items.order_by("presentation_order"))
        assert len(items) == 3

        assert items[0].presentation_order == 1
        assert items[0].question_id == q1_id
        assert items[0].question_version_id == v1_id
        assert items[0].allocated_marks == Decimal("2.50")
        assert items[0].allocated_penalty == Decimal("0.83")

        assert items[1].presentation_order == 2
        assert items[1].question_id == q2_id
        assert items[1].question_version_id == v2_id

        assert items[2].presentation_order == 3
        assert items[2].question_id == q3_id
        assert items[2].question_version_id == v3_id

    def test_paper_generation_deduplication_across_multiple_rules(self):
        assessment = Assessment.objects.create(title="Deduplication Test")
        sec1 = AssessmentSection.objects.create(assessment=assessment, title="Section 1", position=1)
        sec2 = AssessmentSection.objects.create(assessment=assessment, title="Section 2", position=2)

        scope1 = uuid.uuid4()
        scope2 = uuid.uuid4()

        SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=sec1,
            scope_type=ScopeType.TOPIC,
            scope_id=scope1,
            question_count=2,
            position=1,
        )
        SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=sec2,
            scope_type=ScopeType.SUBJECT,
            scope_id=scope2,
            question_count=2,
            position=2,
        )
        assessment.publish()

        # Notice Q2 is present in both candidate pools!
        q1_id, v1_id = uuid.uuid4(), uuid.uuid4()
        q2_id, v2_id = uuid.uuid4(), uuid.uuid4()
        q3_id, v3_id = uuid.uuid4(), uuid.uuid4()
        q4_id, v4_id = uuid.uuid4(), uuid.uuid4()

        port = FakeCandidatePort({
            ("TOPIC", scope1): [
                QuestionCandidateDTO(q1_id, v1_id, "MCQ", "EASY"),
                QuestionCandidateDTO(q2_id, v2_id, "MCQ", "EASY"),
            ],
            ("SUBJECT", scope2): [
                QuestionCandidateDTO(q2_id, v2_id, "MCQ", "EASY"),  # Overlap! Must be skipped
                QuestionCandidateDTO(q3_id, v3_id, "MCQ", "EASY"),
                QuestionCandidateDTO(q4_id, v4_id, "MCQ", "EASY"),
            ],
        })

        paper = generate_paper(assessment.id, port)
        items = list(paper.items.order_by("presentation_order"))
        assert len(items) == 4

        # Q1 and Q2 from rule 1
        assert items[0].question_id == q1_id
        assert items[0].assessment_section_id == sec1.id
        assert items[1].question_id == q2_id
        assert items[1].assessment_section_id == sec1.id

        # Rule 2 selected Q3 and Q4 (skipping duplicate Q2)
        assert items[2].question_id == q3_id
        assert items[2].assessment_section_id == sec2.id
        assert items[3].question_id == q4_id
        assert items[3].assessment_section_id == sec2.id

    def test_insufficient_candidates_rolls_back_entire_paper(self):
        assessment = Assessment.objects.create(title="Insufficient Questions Test")
        scope_id = uuid.uuid4()
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=scope_id,
            question_count=5,  # Requires 5
            position=1,
        )
        assessment.publish()

        # Only 2 candidates available
        port = FakeCandidatePort({
            ("TOPIC", scope_id): [
                QuestionCandidateDTO(uuid.uuid4(), uuid.uuid4(), "MCQ", "EASY"),
                QuestionCandidateDTO(uuid.uuid4(), uuid.uuid4(), "MCQ", "EASY"),
            ]
        })

        with pytest.raises(InsufficientQuestionsError, match="required 5, found 2 eligible"):
            generate_paper(assessment.id, port)

        # Verify atomic rollback: no paper or paper items created in DB
        assert AssessmentPaper.objects.filter(assessment=assessment).count() == 0
        assert AssessmentPaperItem.objects.count() == 0

    def test_generated_paper_and_items_are_immutable(self):
        assessment = Assessment.objects.create(title="Frozen Paper Test")
        scope_id = uuid.uuid4()
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=scope_id,
            question_count=1,
            position=1,
        )
        assessment.publish()

        q_id, v_id = uuid.uuid4(), uuid.uuid4()
        port = FakeCandidatePort({
            ("TOPIC", scope_id): [QuestionCandidateDTO(q_id, v_id, "MCQ", "EASY")]
        })

        paper = generate_paper(assessment.id, port)
        item = paper.items.first()

        # Attempt to modify paper
        paper.duration_seconds = 1000
        with pytest.raises(AssessmentPaperImmutableError):
            paper.save()

        # Attempt to modify item
        item.allocated_marks = Decimal("10.00")
        with pytest.raises(AssessmentPaperImmutableError):
            item.save()

        # Attempt to delete paper
        with pytest.raises(AssessmentPaperImmutableError):
            paper.delete()

        # Attempt to delete item
        with pytest.raises(AssessmentPaperImmutableError):
            item.delete()
