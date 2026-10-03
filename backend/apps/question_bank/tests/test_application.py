import uuid
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.application import (
    approve_question_version,
    archive_question_version,
    create_question,
    create_question_version,
    publish_question_version,
    reject_question_version_to_draft,
    reopen_question_version_review,
    submit_question_version_for_review,
)
from apps.question_bank.exceptions import (
    ContentRepresentationError,
    ImmutableVersionError,
    InvalidStatusTransitionError,
    InvalidTopicError,
    PublicationConflictError,
    PublicationValidationError,
    QuestionBankError,
    VersionCreationConflictError,
)
from apps.question_bank.models import (
    AssertionReasonRelationship,
    Difficulty,
    MatchItemSide,
    Question,
    QuestionSourceType,
    QuestionStatus,
    QuestionType,
    QuestionVersion,
)


@pytest.fixture
def sample_topic():
    domain = Domain.objects.create(name="Civil Services App")
    subject = Subject.objects.create(domain=domain, name="Polity App")
    chapter = Chapter.objects.create(subject=subject, name="Preamble App")
    return Topic.objects.create(chapter=chapter, name="Sovereignty App")


@pytest.fixture
def second_topic(sample_topic):
    return Topic.objects.create(
        chapter=sample_topic.chapter,
        name="Secularism App",
    )


@pytest.mark.django_db
class TestCreateQuestionUseCase:
    """Tests for the create_question application operation."""

    @pytest.mark.parametrize(
        "q_type,content_kwargs",
        [
            (
                QuestionType.MCQ,
                {
                    "choices": [
                        {"text": "Choice 1", "position": 1, "is_correct": True},
                        {"text": "Choice 2", "position": 2, "is_correct": False},
                    ]
                },
            ),
            (
                QuestionType.MULTIPLE_SELECT,
                {
                    "choices": [
                        {"text": "Choice A", "position": 1, "is_correct": True},
                        {"text": "Choice B", "position": 2, "is_correct": True},
                        {"text": "Choice C", "position": 3, "is_correct": False},
                    ]
                },
            ),
            (
                QuestionType.TRUE_FALSE,
                {
                    "true_false_data": {"answer": True},
                },
            ),
            (
                QuestionType.ASSERTION_REASON,
                {
                    "assertion_reason_data": {
                        "assertion": "India is a sovereign state.",
                        "reason": "It has independent authority to legislate.",
                        "correct_relationship": AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
                    }
                },
            ),
            (
                QuestionType.MATCH_FOLLOWING,
                {
                    "match_following_data": {
                        "left_items": [{"text": "Article 14", "position": 1}, {"text": "Article 19", "position": 2}],
                        "right_items": [{"text": "Right to Equality", "position": 1}, {"text": "Right to Freedom", "position": 2}],
                        "pairs": [{"left": 1, "right": 1}, {"left": 2, "right": 2}],
                    }
                },
            ),
            (
                QuestionType.DESCRIPTIVE,
                {
                    "descriptive_data": {
                        "marks": 10,
                        "expected_answer": "Detailed answer regarding basic structure doctrine.",
                    }
                },
            ),
        ],
    )
    def test_create_question_all_six_types(self, sample_topic, q_type, content_kwargs):
        """Create question supports all six question types with their valid representations."""
        q = create_question(
            question_type=q_type,
            text=f"Question text for {q_type}",
            difficulty=Difficulty.MEDIUM,
            explanation=f"Explanation for {q_type}",
            topic_ids=[sample_topic.id],
            source_type=QuestionSourceType.ORIGINAL,
            source_name="Nexora Authors",
            **content_kwargs,
        )

        assert isinstance(q, Question)
        v = q.latest_version
        assert v is not None
        assert v.version_number == 1
        assert v.status == QuestionStatus.DRAFT
        assert v.question_type == q_type
        assert v.source_type == QuestionSourceType.ORIGINAL
        assert v.source_name == "Nexora Authors"
        assert q.question_topics.filter(topic=sample_topic).exists()

    def test_create_question_with_full_provenance(self, sample_topic):
        """Provenance metadata is fully captured on initial version."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="UPSC Question",
            difficulty=Difficulty.HARD,
            topic_ids=[sample_topic.id],
            source_type=QuestionSourceType.UPSC_PREVIOUS_YEAR,
            source_name="UPSC CSE",
            source_reference="CSE 2024 GS Paper 1 Q10",
            source_year=2024,
            external_question_id="UPSC-2024-Q10",
            choices=[
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": False},
            ],
        )
        v = q.latest_version
        assert v.source_type == QuestionSourceType.UPSC_PREVIOUS_YEAR
        assert v.source_name == "UPSC CSE"
        assert v.source_reference == "CSE 2024 GS Paper 1 Q10"
        assert v.source_year == 2024
        assert v.external_question_id == "UPSC-2024-Q10"

    def test_create_question_invalid_topic_rejected_and_rolled_back(self):
        """Non-existent topic ID causes transaction rollback; no question is persisted."""
        fake_topic_id = uuid.uuid4()
        with pytest.raises(InvalidTopicError):
            create_question(
                question_type=QuestionType.MCQ,
                text="Some text",
                difficulty=Difficulty.EASY,
                topic_ids=[fake_topic_id],
                choices=[{"text": "Opt 1", "is_correct": True}, {"text": "Opt 2", "is_correct": False}],
            )

        assert Question.objects.count() == 0
        assert QuestionVersion.objects.count() == 0

    def test_create_question_malformed_topic_uuid_rejected(self):
        """Malformed topic string raises InvalidTopicError."""
        with pytest.raises(InvalidTopicError):
            create_question(
                question_type=QuestionType.MCQ,
                text="Some text",
                difficulty=Difficulty.EASY,
                topic_ids=["not-a-valid-uuid"],
                choices=[{"text": "Opt 1", "is_correct": True}, {"text": "Opt 2", "is_correct": False}],
            )

        assert Question.objects.count() == 0

    def test_create_question_incompatible_content_rejected_and_rolled_back(self, sample_topic):
        """Supplying incompatible content payload triggers ContentRepresentationError and rolls back."""
        with pytest.raises(ContentRepresentationError):
            create_question(
                question_type=QuestionType.MCQ,
                text="MCQ question",
                difficulty=Difficulty.EASY,
                topic_ids=[sample_topic.id],
                descriptive_data={"marks": 5, "expected_answer": "Answer"},  # wrong content
            )

        assert Question.objects.count() == 0
        assert QuestionVersion.objects.count() == 0

    def test_create_question_empty_text_rejected_and_rolled_back(self, sample_topic):
        """Model validation failure rolls back the entire atomic operation."""
        with pytest.raises(ValidationError):
            create_question(
                question_type=QuestionType.MCQ,
                text="   ",
                difficulty=Difficulty.EASY,
                topic_ids=[sample_topic.id],
                choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
            )

        assert Question.objects.count() == 0


@pytest.mark.django_db
class TestCreateQuestionVersionUseCase:
    """Tests for the create_question_version application operation."""

    def test_create_next_version_increments_version_number(self, sample_topic):
        """New versions receive sequential version numbers and start as DRAFT."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Version 1 text",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        assert q.latest_version.version_number == 1

        v2 = create_question_version(
            q,
            question_type=QuestionType.MCQ,
            text="Version 2 updated text",
            difficulty=Difficulty.MEDIUM,
            choices=[{"text": "A2", "is_correct": True}, {"text": "B2", "is_correct": False}],
        )
        assert v2.version_number == 2
        assert v2.status == QuestionStatus.DRAFT
        assert q.versions.count() == 2

        v3 = create_question_version(
            q.id,
            question_type=QuestionType.MCQ,
            text="Version 3 text",
            difficulty=Difficulty.HARD,
            choices=[{"text": "A3", "is_correct": True}, {"text": "B3", "is_correct": False}],
        )
        assert v3.version_number == 3
        assert q.versions.count() == 3

    def test_create_question_version_does_not_mutate_prior_versions(self, sample_topic):
        """Prior versions remain unchanged when a new version is created."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Original version text",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v1 = q.latest_version

        create_question_version(
            q,
            question_type=QuestionType.MCQ,
            text="Completely different text for v2",
            difficulty=Difficulty.HARD,
            choices=[{"text": "X", "is_correct": True}, {"text": "Y", "is_correct": False}],
        )

        v1.refresh_from_db()
        assert v1.text == "Original version text"
        assert v1.difficulty == Difficulty.EASY
        assert v1.version_number == 1

    def test_create_question_version_syncs_topics_if_specified(self, sample_topic, second_topic):
        """Specifying topic_ids on version creation updates question topics."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Text",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        assert q.question_topics.count() == 1

        create_question_version(
            q,
            question_type=QuestionType.MCQ,
            text="Text v2",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id, second_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )

        assert q.question_topics.count() == 2

    def test_create_question_version_rolls_back_on_content_failure(self, sample_topic):
        """If content creation fails, new version is not persisted."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Text v1",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        assert q.versions.count() == 1

        with pytest.raises(ContentRepresentationError):
            create_question_version(
                q,
                question_type=QuestionType.MCQ,
                text="Text v2",
                difficulty=Difficulty.EASY,
                choices=[],  # empty choices
            )

        assert q.versions.count() == 1

    def test_create_question_version_nonexistent_question_raises(self):
        """Attempting to create version for non-existent question raises QuestionBankError."""
        fake_id = uuid.uuid4()
        with pytest.raises(QuestionBankError) as exc:
            create_question_version(
                fake_id,
                question_type=QuestionType.MCQ,
                text="Text",
                difficulty=Difficulty.EASY,
                choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
            )
        assert "does not exist" in str(exc.value)

    def test_version_creation_conflict_error_translated(self, sample_topic):
        """Simulated concurrent uniqueness collision translates to VersionCreationConflictError."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Text",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )

        with patch.object(
            QuestionVersion,
            "save",
            side_effect=IntegrityError("duplicate key value violates unique constraint \"unique_question_version_number\""),
        ):
            with pytest.raises(VersionCreationConflictError):
                create_question_version(
                    q,
                    question_type=QuestionType.MCQ,
                    text="Text v2",
                    difficulty=Difficulty.EASY,
                    choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
                )


@pytest.mark.django_db
class TestLifecycleUseCases:
    """Tests for discrete lifecycle state transition operations."""

    def test_full_lifecycle_progression(self, sample_topic):
        """DRAFT -> REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED succeeds."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question for lifecycle",
            difficulty=Difficulty.MEDIUM,
            topic_ids=[sample_topic.id],
            choices=[{"text": "Correct", "is_correct": True}, {"text": "Incorrect", "is_correct": False}],
        )
        v = q.latest_version
        assert v.status == QuestionStatus.DRAFT

        # 1. Submit for review
        v = submit_question_version_for_review(v)
        assert v.status == QuestionStatus.REVIEW

        # 2. Approve
        v = approve_question_version(v)
        assert v.status == QuestionStatus.APPROVED

        # 3. Publish
        v = publish_question_version(v)
        assert v.status == QuestionStatus.PUBLISHED

        # 4. Archive
        v = archive_question_version(v)
        assert v.status == QuestionStatus.ARCHIVED

    def test_reverse_transitions(self, sample_topic):
        """REVIEW -> DRAFT and APPROVED -> REVIEW are supported."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version

        # DRAFT -> REVIEW -> DRAFT
        v = submit_question_version_for_review(v)
        assert v.status == QuestionStatus.REVIEW
        v = reject_question_version_to_draft(v)
        assert v.status == QuestionStatus.DRAFT

        # DRAFT -> REVIEW -> APPROVED -> REVIEW
        v = submit_question_version_for_review(v)
        v = approve_question_version(v)
        assert v.status == QuestionStatus.APPROVED
        v = reopen_question_version_review(v)
        assert v.status == QuestionStatus.REVIEW

    def test_invalid_lifecycle_transition_raises_error(self, sample_topic):
        """Illegal transitions raise InvalidStatusTransitionError."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version

        # DRAFT cannot jump directly to APPROVED or PUBLISHED
        with pytest.raises(InvalidStatusTransitionError):
            approve_question_version(v)

        with pytest.raises(InvalidStatusTransitionError):
            publish_question_version(v)

    def test_terminal_archived_status_cannot_transition(self, sample_topic):
        """ARCHIVED status is terminal and cannot transition to any other status."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        submit_question_version_for_review(v)
        approve_question_version(v)
        publish_question_version(v)
        archive_question_version(v)

        with pytest.raises(InvalidStatusTransitionError):
            submit_question_version_for_review(v)

    def test_immutable_versions_cannot_be_mutated(self, sample_topic):
        """Approved and published versions reject content edits."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        submit_question_version_for_review(v)
        approve_question_version(v)

        v.text = "Attempted edit on approved version"
        with pytest.raises(ImmutableVersionError):
            v.save()

    def test_lifecycle_operations_accept_question_or_id(self, sample_topic):
        """Lifecycle operations accept Question instance, UUID, or UUID string."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v_id = q.latest_version.id

        # Pass by Question instance
        v = submit_question_version_for_review(q)
        assert v.status == QuestionStatus.REVIEW

        # Pass by UUID instance
        v = approve_question_version(v_id)
        assert v.status == QuestionStatus.APPROVED

        # Pass by UUID string
        v = publish_question_version(str(v_id))
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestPublishUseCase:
    """Tests for the publish_question_version application operation."""

    def test_publish_enforces_publication_completeness(self, sample_topic):
        """Incomplete questions (e.g. MCQ with no correct choices) cannot be published."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": False}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        submit_question_version_for_review(v)
        approve_question_version(v)

        with pytest.raises(PublicationValidationError):
            publish_question_version(v)

    def test_publish_requires_topic_association(self):
        """Questions without topics cannot be published."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Question",
            difficulty=Difficulty.EASY,
            topic_ids=None,  # No topics
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        submit_question_version_for_review(v)
        approve_question_version(v)

        with pytest.raises(PublicationValidationError) as exc:
            publish_question_version(v)
        assert "associated with at least one Learning Topic" in str(exc.value)

    def test_only_one_published_version_per_question(self, sample_topic):
        """Publishing a second version while one is already published raises PublicationConflictError."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Version 1",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v1 = q.latest_version
        submit_question_version_for_review(v1)
        approve_question_version(v1)
        publish_question_version(v1)

        # Create and approve version 2
        v2 = create_question_version(
            q,
            question_type=QuestionType.MCQ,
            text="Version 2",
            difficulty=Difficulty.EASY,
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        submit_question_version_for_review(v2)
        approve_question_version(v2)

        # Attempting to publish v2 while v1 is published must fail
        with pytest.raises(PublicationConflictError) as exc:
            publish_question_version(v2)
        assert "already has a published version" in str(exc.value)

    def test_archiving_published_version_allows_publishing_new_version(self, sample_topic):
        """Archiving the currently published version allows publishing a subsequent version."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Version 1",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v1 = q.latest_version
        submit_question_version_for_review(v1)
        approve_question_version(v1)
        publish_question_version(v1)

        # Archive version 1
        archive_question_version(v1)

        # Version 2 can now be published
        v2 = create_question_version(
            q,
            question_type=QuestionType.MCQ,
            text="Version 2",
            difficulty=Difficulty.EASY,
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        submit_question_version_for_review(v2)
        approve_question_version(v2)
        publish_question_version(v2)

        assert v2.status == QuestionStatus.PUBLISHED
        assert q.published_version == v2

    def test_concurrent_publication_conflict_translated(self, sample_topic):
        """Simulated concurrent publication conflict raises PublicationConflictError."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Version 1",
            difficulty=Difficulty.EASY,
            topic_ids=[sample_topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        submit_question_version_for_review(v)
        approve_question_version(v)

        with patch(
            "apps.question_bank.application.lifecycle.transition_question_version_status",
            side_effect=IntegrityError("duplicate key value violates unique constraint \"unique_published_version_per_question\""),
        ):
            with pytest.raises(PublicationConflictError):
                publish_question_version(v)
