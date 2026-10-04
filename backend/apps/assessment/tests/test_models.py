import uuid
from decimal import Decimal
import pytest
from django.db import IntegrityError

from apps.assessment.exceptions import (
    AssessmentPaperImmutableError,
    AssessmentValidationError,
)
from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentSection,
    AssessmentStatus,
    AssessmentType,
    PaperStatus,
    QuestionType,
    ScopeType,
    SelectionRule,
)


@pytest.mark.django_db
class TestAssessmentModels:
    def test_create_assessment_defaults(self):
        assessment = Assessment.objects.create(
            title="General Studies Prelims Mock",
            description="Complete paper for test practice",
        )
        assert assessment.id is not None
        assert assessment.status == AssessmentStatus.DRAFT
        assert assessment.type == AssessmentType.PRACTICE
        assert assessment.duration_seconds == 3600
        assert assessment.marks_per_question == Decimal("2.00")
        assert assessment.penalty_per_question == Decimal("0.66")
        assert assessment.can_edit() is True
        assert str(assessment) == "General Studies Prelims Mock (DRAFT)"

    def test_assessment_section_creation_and_ordering(self):
        assessment = Assessment.objects.create(title="Multi-Section Test")
        sec1 = AssessmentSection.objects.create(assessment=assessment, title="History", position=1)
        sec2 = AssessmentSection.objects.create(assessment=assessment, title="Geography", position=2)

        sections = list(assessment.sections.all())
        assert sections == [sec1, sec2]
        assert str(sec1) == "Multi-Section Test - Section 1: History"

    def test_assessment_section_unique_position(self):
        assessment = Assessment.objects.create(title="Section Collision Test")
        AssessmentSection.objects.create(assessment=assessment, title="Sec A", position=1)
        from django.db import transaction
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                AssessmentSection.objects.create(assessment=assessment, title="Sec B", position=1)

    def test_selection_rule_creation_and_validation(self):
        assessment = Assessment.objects.create(title="Rule Test")
        scope_uuid = uuid.uuid4()
        rule = SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=scope_uuid,
            question_type=QuestionType.MCQ,
            question_count=10,
            position=1,
        )
        assert rule.id is not None
        assert rule.question_count == 10
        assert rule.position == 1

    def test_selection_rule_zero_count_rejected(self):
        assessment = Assessment.objects.create(title="Invalid Rule Count")
        with pytest.raises(AssessmentValidationError):
            SelectionRule.objects.create(
                assessment=assessment,
                scope_type=ScopeType.TOPIC,
                scope_id=uuid.uuid4(),
                question_count=0,
                position=1,
            )

    def test_selection_rule_mismatched_section_rejected(self):
        assessment1 = Assessment.objects.create(title="Assessment 1")
        assessment2 = Assessment.objects.create(title="Assessment 2")
        sec_of_a2 = AssessmentSection.objects.create(assessment=assessment2, title="Sec", position=1)

        with pytest.raises(AssessmentValidationError):
            SelectionRule.objects.create(
                assessment=assessment1,
                assessment_section=sec_of_a2,
                scope_type=ScopeType.TOPIC,
                scope_id=uuid.uuid4(),
                question_count=5,
                position=1,
            )

    def test_selection_rule_unique_position(self):
        assessment = Assessment.objects.create(title="Rule Collision")
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=5,
            position=1,
        )
        from django.db import transaction
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                SelectionRule.objects.create(
                    assessment=assessment,
                    scope_type=ScopeType.CHAPTER,
                    scope_id=uuid.uuid4(),
                    question_count=3,
                    position=1,
                )

    def test_assessment_paper_creation_and_immutability(self):
        assessment = Assessment.objects.create(
            title="Paper Immutability Test",
            duration_seconds=7200,
            marks_per_question=Decimal("4.00"),
            penalty_per_question=Decimal("1.00"),
        )
        paper = AssessmentPaper.objects.create(
            assessment=assessment,
            status=PaperStatus.GENERATED,
            duration_seconds=assessment.duration_seconds,
            marks_per_question=assessment.marks_per_question,
            penalty_per_question=assessment.penalty_per_question,
        )
        assert paper.id is not None
        assert paper.duration_seconds == 7200
        assert paper.marks_per_question == Decimal("4.00")
        assert paper.penalty_per_question == Decimal("1.00")

        # Mutating existing paper raises AssessmentPaperImmutableError
        paper.duration_seconds = 3600
        with pytest.raises(AssessmentPaperImmutableError):
            paper.save()

        # Deleting paper raises AssessmentPaperImmutableError
        with pytest.raises(AssessmentPaperImmutableError):
            paper.delete()

    def test_paper_item_creation_and_constraints(self):
        assessment = Assessment.objects.create(title="Paper Item Test")
        paper = AssessmentPaper.objects.create(
            assessment=assessment,
            duration_seconds=3600,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.66"),
        )
        q1_id = uuid.uuid4()
        v1_id = uuid.uuid4()

        item = AssessmentPaperItem.objects.create(
            paper=paper,
            question_id=q1_id,
            question_version_id=v1_id,
            presentation_order=1,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.66"),
        )
        assert item.id is not None

        # Duplicate presentation_order raises IntegrityError
        from django.db import transaction
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                AssessmentPaperItem.objects.create(
                    paper=paper,
                    question_id=uuid.uuid4(),
                    question_version_id=uuid.uuid4(),
                    presentation_order=1,
                    allocated_marks=Decimal("2.00"),
                    allocated_penalty=Decimal("0.66"),
                )

        # Duplicate question_id on the same paper raises IntegrityError
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                AssessmentPaperItem.objects.create(
                    paper=paper,
                    question_id=q1_id,
                    question_version_id=uuid.uuid4(),
                    presentation_order=2,
                    allocated_marks=Decimal("2.00"),
                    allocated_penalty=Decimal("0.66"),
                )

        # Updating item raises AssessmentPaperImmutableError
        item.allocated_marks = Decimal("5.00")
        with pytest.raises(AssessmentPaperImmutableError):
            item.save()

        # Deleting item raises AssessmentPaperImmutableError
        with pytest.raises(AssessmentPaperImmutableError):
            item.delete()
