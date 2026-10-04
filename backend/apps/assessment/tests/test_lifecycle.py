import uuid
from decimal import Decimal
import pytest

from apps.assessment.application.lifecycle import archive_assessment, publish_assessment
from apps.assessment.exceptions import (
    AssessmentImmutableError,
    AssessmentValidationError,
    InvalidStatusTransitionError,
)
from apps.assessment.models import (
    Assessment,
    AssessmentSection,
    AssessmentStatus,
    ScopeType,
    SelectionRule,
)


@pytest.mark.django_db
class TestAssessmentLifecycle:
    def test_publish_without_selection_rules_rejected(self):
        assessment = Assessment.objects.create(title="Empty Assessment")
        with pytest.raises(AssessmentValidationError, match="without at least one selection rule"):
            publish_assessment(assessment.id)

    def test_publish_with_invalid_duration_rejected(self):
        assessment = Assessment.objects.create(title="Zero Duration Assessment", duration_seconds=0)
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=5,
            position=1,
        )
        with pytest.raises(AssessmentValidationError, match="duration must be greater than 0"):
            publish_assessment(assessment.id)

    def test_publish_with_invalid_marks_rejected(self):
        assessment = Assessment.objects.create(
            title="Zero Marks Assessment",
            marks_per_question=Decimal("0.00"),
        )
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=5,
            position=1,
        )
        with pytest.raises(AssessmentValidationError, match="Marks per question must be greater than 0"):
            publish_assessment(assessment.id)

    def test_successful_publish_and_archive(self):
        assessment = Assessment.objects.create(title="Valid Assessment")
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=10,
            position=1,
        )
        # Publish
        published = publish_assessment(assessment.id)
        assert published.status == AssessmentStatus.PUBLISHED
        assert published.can_edit() is False

        # Archive
        archived = archive_assessment(assessment.id)
        assert archived.status == AssessmentStatus.ARCHIVED
        assert archived.can_edit() is False

    def test_invalid_transitions_rejected(self):
        # DRAFT -> ARCHIVED directly is invalid
        draft = Assessment.objects.create(title="Draft")
        with pytest.raises(InvalidStatusTransitionError):
            draft.archive()

        # PUBLISHED -> DRAFT is invalid
        assessment = Assessment.objects.create(title="Pub")
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=10,
            position=1,
        )
        assessment.publish()
        with pytest.raises(InvalidStatusTransitionError):
            assessment.status = AssessmentStatus.DRAFT
            assessment.save()
        assessment.refresh_from_db()

        # ARCHIVED -> PUBLISHED is invalid
        assessment.archive()
        with pytest.raises(InvalidStatusTransitionError):
            assessment.publish()

    def test_modifying_published_assessment_rejected(self):
        assessment = Assessment.objects.create(title="Immutable Published")
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=10,
            position=1,
        )
        assessment.publish()

        assessment.title = "New Title"
        with pytest.raises(AssessmentImmutableError):
            assessment.save()

    def test_modifying_archived_assessment_rejected(self):
        assessment = Assessment.objects.create(title="Immutable Archived")
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=10,
            position=1,
        )
        assessment.publish()
        assessment.archive()

        assessment.title = "Attempted Change"
        with pytest.raises(AssessmentImmutableError):
            assessment.save()

    def test_modifying_sections_on_published_assessment_rejected(self):
        assessment = Assessment.objects.create(title="Assessment with Section")
        sec = AssessmentSection.objects.create(assessment=assessment, title="Section 1", position=1)
        SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=sec,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=5,
            position=1,
        )
        assessment.publish()

        # Adding section rejected
        with pytest.raises(AssessmentImmutableError):
            AssessmentSection.objects.create(assessment=assessment, title="Section 2", position=2)

        # Modifying section rejected
        sec.title = "Changed Title"
        with pytest.raises(AssessmentImmutableError):
            sec.save()

        # Deleting section rejected
        with pytest.raises(AssessmentImmutableError):
            sec.delete()

    def test_modifying_rules_on_published_assessment_rejected(self):
        assessment = Assessment.objects.create(title="Assessment with Rule")
        rule = SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=5,
            position=1,
        )
        assessment.publish()

        # Adding rule rejected
        with pytest.raises(AssessmentImmutableError):
            SelectionRule.objects.create(
                assessment=assessment,
                scope_type=ScopeType.CHAPTER,
                scope_id=uuid.uuid4(),
                question_count=2,
                position=2,
            )

        # Modifying rule rejected
        rule.question_count = 10
        with pytest.raises(AssessmentImmutableError):
            rule.save()

        # Deleting rule rejected
        with pytest.raises(AssessmentImmutableError):
            rule.delete()
