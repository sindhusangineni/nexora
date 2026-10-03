import pytest
from django.core.exceptions import ValidationError

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.exceptions import ImmutableVersionError
from apps.question_bank.models import (
    Difficulty,
    Question,
    QuestionSourceType,
    QuestionStatus,
    QuestionTopic,
    QuestionType,
    QuestionVersion,
    QuestionVersionChoice,
)
from apps.question_bank.services.lifecycle import transition_question_version_status


@pytest.fixture
def topic():
    domain = Domain.objects.create(name="Civil Services")
    subject = Subject.objects.create(domain=domain, name="Indian Polity")
    chapter = Chapter.objects.create(subject=subject, name="Fundamental Rights")
    return Topic.objects.create(chapter=chapter, name="Right to Equality")


@pytest.fixture
def question(topic):
    q = Question.objects.create()
    QuestionTopic.objects.create(question=q, topic=topic)
    return q


@pytest.mark.django_db
class TestProvenanceMetadata:
    """
    Tests for Phase 1.1 minimal provenance metadata on QuestionVersion.
    """

    @pytest.mark.parametrize(
        "source_type",
        [
            QuestionSourceType.ORIGINAL,
            QuestionSourceType.UPSC_PREVIOUS_YEAR,
            QuestionSourceType.LICENSED,
            QuestionSourceType.CONTRIBUTOR,
            QuestionSourceType.AI_GENERATED,
            QuestionSourceType.IMPORTED,
        ],
    )
    def test_each_source_type_is_accepted(self, question, source_type):
        """1. Each defined QuestionSourceType choice is accepted and valid."""
        version = QuestionVersion(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Test question with source type",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
            source_type=source_type,
        )
        version.full_clean()
        version.save()

        persisted = QuestionVersion.objects.get(pk=version.pk)
        assert persisted.source_type == source_type

    def test_invalid_source_type_rejected(self, question):
        """Invalid source_type values are rejected during model validation."""
        version = QuestionVersion(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Invalid source type question",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
            source_type="INVALID_SOURCE",
        )
        with pytest.raises(ValidationError):
            version.full_clean()

    def test_provenance_fields_are_optional(self, question):
        """2. All provenance fields may be omitted and default to None."""
        version = QuestionVersion.objects.create(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Question with omitted provenance",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        version.full_clean()

        persisted = QuestionVersion.objects.get(pk=version.pk)
        assert persisted.source_type is None
        assert persisted.source_name is None
        assert persisted.source_reference is None
        assert persisted.source_year is None
        assert persisted.external_question_id is None

    def test_provenance_values_persisted_correctly(self, question):
        """3. All provenance fields are persisted and reloaded correctly."""
        version = QuestionVersion.objects.create(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="UPSC CSE 2024 Prelims Question",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
            source_type=QuestionSourceType.UPSC_PREVIOUS_YEAR,
            source_name="UPSC Civil Services Examination",
            source_reference="CSE 2024 Prelims GS Paper 1, Question 42",
            source_year=2024,
            external_question_id="UPSC-2024-GS1-042",
        )
        version.full_clean()

        persisted = QuestionVersion.objects.get(pk=version.pk)
        assert persisted.source_type == QuestionSourceType.UPSC_PREVIOUS_YEAR
        assert persisted.source_name == "UPSC Civil Services Examination"
        assert persisted.source_reference == "CSE 2024 Prelims GS Paper 1, Question 42"
        assert persisted.source_year == 2024
        assert persisted.external_question_id == "UPSC-2024-GS1-042"

    def test_provenance_lifecycle_preservation(self, question):
        """4. Existing QuestionVersion lifecycle behavior preserves provenance metadata."""
        version = QuestionVersion.objects.create(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="AI-generated practice question",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
            source_type=QuestionSourceType.AI_GENERATED,
            source_name="Nexora AI Generation",
            source_reference="Batch 2026-Q1",
            source_year=2026,
            external_question_id="AI-GEN-8891",
        )
        # Add valid choices for publication
        QuestionVersionChoice.objects.create(
            question_version=version,
            position=1,
            text="Option A",
            is_correct=True,
        )
        QuestionVersionChoice.objects.create(
            question_version=version,
            position=2,
            text="Option B",
            is_correct=False,
        )

        # Transition through complete lifecycle
        transition_question_version_status(version, QuestionStatus.REVIEW)
        version.refresh_from_db()
        assert version.status == QuestionStatus.REVIEW
        assert version.source_type == QuestionSourceType.AI_GENERATED
        assert version.source_name == "Nexora AI Generation"
        assert version.source_year == 2026

        transition_question_version_status(version, QuestionStatus.APPROVED)
        version.refresh_from_db()
        assert version.status == QuestionStatus.APPROVED
        assert version.source_reference == "Batch 2026-Q1"

        transition_question_version_status(version, QuestionStatus.PUBLISHED)
        version.refresh_from_db()
        assert version.status == QuestionStatus.PUBLISHED
        assert version.external_question_id == "AI-GEN-8891"

        transition_question_version_status(version, QuestionStatus.ARCHIVED)
        version.refresh_from_db()
        assert version.status == QuestionStatus.ARCHIVED
        assert version.source_type == QuestionSourceType.AI_GENERATED

    @pytest.mark.parametrize(
        "field_to_modify,new_value",
        [
            ("source_type", QuestionSourceType.LICENSED),
            ("source_name", "Altered Source"),
            ("source_reference", "Altered Ref"),
            ("source_year", 2020),
            ("external_question_id", "ALT-001"),
        ],
    )
    def test_provenance_immutability_on_approved_or_published(
        self, question, field_to_modify, new_value
    ):
        """Approved and published versions protect provenance fields from mutation."""
        version = QuestionVersion.objects.create(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Original contributor question",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
            source_type=QuestionSourceType.CONTRIBUTOR,
            source_name="Faculty Contributor A",
            source_reference="Internal Submissions 2025",
            source_year=2025,
            external_question_id="CONTRIB-001",
        )
        QuestionVersionChoice.objects.create(
            question_version=version,
            position=1,
            text="Correct Choice",
            is_correct=True,
        )
        QuestionVersionChoice.objects.create(
            question_version=version,
            position=2,
            text="Incorrect Choice",
            is_correct=False,
        )

        transition_question_version_status(version, QuestionStatus.REVIEW)
        transition_question_version_status(version, QuestionStatus.APPROVED)
        version.refresh_from_db()

        setattr(version, field_to_modify, new_value)
        with pytest.raises(ImmutableVersionError):
            version.save()

    def test_publication_validation_works_with_and_without_provenance(self, question):
        """5. Existing publication validation rules still work with or without provenance."""
        # Version with invalid choices (0 correct choices for MCQ) fails PublicationValidationError
        v1 = QuestionVersion.objects.create(
            question=question,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Incomplete question",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
            source_type=QuestionSourceType.ORIGINAL,
            source_name="Nexora Authors",
            source_year=2026,
        )
        QuestionVersionChoice.objects.create(
            question_version=v1,
            position=1,
            text="Option 1",
            is_correct=False,
        )
        QuestionVersionChoice.objects.create(
            question_version=v1,
            position=2,
            text="Option 2",
            is_correct=False,
        )

        transition_question_version_status(v1, QuestionStatus.REVIEW)
        transition_question_version_status(v1, QuestionStatus.APPROVED)

        # Attempting to publish without correct choice must fail with PublicationValidationError
        from apps.question_bank.exceptions import PublicationValidationError

        with pytest.raises(PublicationValidationError):
            transition_question_version_status(v1, QuestionStatus.PUBLISHED)
