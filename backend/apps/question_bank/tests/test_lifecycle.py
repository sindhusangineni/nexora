import pytest
from django.db.models.deletion import ProtectedError

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.exceptions import (
    ImmutableVersionError,
    InvalidStatusTransitionError,
)
from apps.question_bank.models import (
    Difficulty,
    Question,
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
def question_with_topic(topic):
    q = Question.objects.create()
    QuestionTopic.objects.create(question=q, topic=topic)
    return q


@pytest.mark.django_db
class TestLifecycleTransitions:
    def test_all_valid_transitions(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Which article guarantees equality?",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="Art 14", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="Art 19", position=2, is_correct=False)

        # 1. DRAFT -> REVIEW
        transition_question_version_status(v, QuestionStatus.REVIEW)
        assert v.status == QuestionStatus.REVIEW

        # 2. REVIEW -> DRAFT
        transition_question_version_status(v, QuestionStatus.DRAFT)
        assert v.status == QuestionStatus.DRAFT

        # DRAFT -> REVIEW again
        transition_question_version_status(v, QuestionStatus.REVIEW)
        assert v.status == QuestionStatus.REVIEW

        # 3. REVIEW -> APPROVED
        transition_question_version_status(v, QuestionStatus.APPROVED)
        assert v.status == QuestionStatus.APPROVED

        # 4. APPROVED -> REVIEW
        transition_question_version_status(v, QuestionStatus.REVIEW)
        assert v.status == QuestionStatus.REVIEW

        # REVIEW -> APPROVED again
        transition_question_version_status(v, QuestionStatus.APPROVED)
        assert v.status == QuestionStatus.APPROVED

        # 5. APPROVED -> PUBLISHED
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED

        # 6. PUBLISHED -> ARCHIVED
        transition_question_version_status(v, QuestionStatus.ARCHIVED)
        assert v.status == QuestionStatus.ARCHIVED

    def test_invalid_transitions_rejected(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Sample question",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )

        # DRAFT -> APPROVED (must fail)
        with pytest.raises(InvalidStatusTransitionError):
            transition_question_version_status(v, QuestionStatus.APPROVED)

        # DRAFT -> PUBLISHED (must fail)
        with pytest.raises(InvalidStatusTransitionError):
            transition_question_version_status(v, QuestionStatus.PUBLISHED)

        # Move to REVIEW
        transition_question_version_status(v, QuestionStatus.REVIEW)

        # REVIEW -> PUBLISHED (must fail)
        with pytest.raises(InvalidStatusTransitionError):
            transition_question_version_status(v, QuestionStatus.PUBLISHED)

        # Move to APPROVED then PUBLISHED
        transition_question_version_status(v, QuestionStatus.APPROVED)
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)

        # PUBLISHED -> DRAFT (must fail)
        with pytest.raises(InvalidStatusTransitionError):
            transition_question_version_status(v, QuestionStatus.DRAFT)

        # Move to ARCHIVED (terminal state)
        transition_question_version_status(v, QuestionStatus.ARCHIVED)

        # ARCHIVED -> DRAFT (must fail)
        with pytest.raises(InvalidStatusTransitionError):
            transition_question_version_status(v, QuestionStatus.DRAFT)

        # ARCHIVED -> PUBLISHED (must fail)
        with pytest.raises(InvalidStatusTransitionError):
            transition_question_version_status(v, QuestionStatus.PUBLISHED)


@pytest.mark.django_db
class TestDirectStatusMutationAttempts:
    def test_draft_to_published_directly_fails(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Draft MCQ",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        v.status = QuestionStatus.PUBLISHED
        with pytest.raises(InvalidStatusTransitionError) as exc:
            v.save()
        assert "Invalid question version status transition from 'DRAFT' to 'PUBLISHED'" in str(exc.value)

    def test_draft_to_approved_directly_fails(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Draft MCQ",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        v.status = QuestionStatus.APPROVED
        with pytest.raises(InvalidStatusTransitionError) as exc:
            v.save()
        assert "Invalid question version status transition from 'DRAFT' to 'APPROVED'" in str(exc.value)

    def test_review_to_published_directly_fails(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Draft MCQ",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        transition_question_version_status(v, QuestionStatus.REVIEW)
        v.status = QuestionStatus.PUBLISHED
        with pytest.raises(InvalidStatusTransitionError) as exc:
            v.save()
        assert "Invalid question version status transition from 'REVIEW' to 'PUBLISHED'" in str(exc.value)

    def test_published_to_draft_directly_fails(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="MCQ",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)

        v.status = QuestionStatus.DRAFT
        with pytest.raises(InvalidStatusTransitionError) as exc:
            v.save()
        assert "Invalid question version status transition from 'PUBLISHED' to 'DRAFT'" in str(exc.value)

    def test_archived_to_anything_directly_fails(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="MCQ",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        transition_question_version_status(v, QuestionStatus.ARCHIVED)

        for target in (QuestionStatus.DRAFT, QuestionStatus.REVIEW, QuestionStatus.APPROVED, QuestionStatus.PUBLISHED):
            v.status = target
            with pytest.raises(InvalidStatusTransitionError):
                v.save()

    def test_direct_creation_with_non_draft_status_fails(self, question_with_topic):
        for illegal_status in (
            QuestionStatus.REVIEW,
            QuestionStatus.APPROVED,
            QuestionStatus.PUBLISHED,
            QuestionStatus.ARCHIVED,
        ):
            with pytest.raises(InvalidStatusTransitionError) as exc:
                QuestionVersion.objects.create(
                    question=question_with_topic,
                    version_number=99,
                    question_type=QuestionType.MCQ,
                    text="Illegal non-draft creation",
                    difficulty=Difficulty.EASY,
                    status=illegal_status,
                )
            assert "New question versions must be created in DRAFT status" in str(exc.value)


@pytest.mark.django_db
class TestVersionImmutability:
    def test_draft_version_can_be_edited(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Initial text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        v.text = "Updated draft text"
        v.difficulty = Difficulty.MEDIUM
        v.save()

        v.refresh_from_db()
        assert v.text == "Updated draft text"
        assert v.difficulty == Difficulty.MEDIUM

    def test_approved_version_content_is_immutable(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Approved text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)

        v.text = "Attempted text change"
        with pytest.raises(ImmutableVersionError):
            v.save()

    def test_published_version_content_is_immutable(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Published text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)

        v.difficulty = Difficulty.HARD
        with pytest.raises(ImmutableVersionError):
            v.save()

    def test_archived_version_content_is_immutable(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Archived text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        transition_question_version_status(v, QuestionStatus.ARCHIVED)

        v.version_number = 99
        with pytest.raises(ImmutableVersionError):
            v.save()


@pytest.mark.django_db
class TestVersionDeletionPolicy:
    def test_draft_version_can_be_deleted(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Draft text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        v_id = v.id
        v.delete()
        assert not QuestionVersion.objects.filter(id=v_id).exists()

    def test_approved_version_deletion_is_blocked(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Approved text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)

        with pytest.raises(ProtectedError):
            v.delete()

    def test_published_version_deletion_is_blocked(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Published text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)

        with pytest.raises(ProtectedError):
            v.delete()

    def test_archived_version_deletion_is_blocked(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Archived text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)
        transition_question_version_status(v, QuestionStatus.REVIEW)
        transition_question_version_status(v, QuestionStatus.APPROVED)
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        transition_question_version_status(v, QuestionStatus.ARCHIVED)

        with pytest.raises(ProtectedError):
            v.delete()


@pytest.mark.django_db
class TestVersionIsolationAndHistory:
    def test_modifying_new_version_does_not_mutate_old_version(self, question_with_topic):
        v1 = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Original v1 text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v1, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v1, text="B", position=2, is_correct=False)
        transition_question_version_status(v1, QuestionStatus.REVIEW)
        transition_question_version_status(v1, QuestionStatus.APPROVED)
        transition_question_version_status(v1, QuestionStatus.PUBLISHED)

        v2 = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=2,
            question_type=QuestionType.MCQ,
            text="New draft v2 text",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
        )

        v2.text = "Further edited v2 text"
        v2.save()

        v1.refresh_from_db()
        v2.refresh_from_db()

        assert v1.text == "Original v1 text"
        assert v1.difficulty == Difficulty.EASY
        assert v1.status == QuestionStatus.PUBLISHED

        assert v2.text == "Further edited v2 text"
        assert v2.difficulty == Difficulty.HARD
        assert v2.status == QuestionStatus.DRAFT
