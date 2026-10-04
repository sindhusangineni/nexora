import uuid
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.models import (
    AssertionReasonContent,
    AssertionReasonRelationship,
    DescriptiveContent,
    Difficulty,
    MatchFollowingContent,
    MatchFollowingItem,
    MatchFollowingPair,
    MatchItemSide,
    Question,
    QuestionStatus,
    QuestionTopic,
    QuestionType,
    QuestionVersion,
    QuestionVersionChoice,
    TrueFalseContent,
)
from apps.question_bank.services.lifecycle import transition_question_version_status


@pytest.fixture
def topic():
    domain = Domain.objects.create(name="Civil Services")
    subject = Subject.objects.create(domain=domain, name="Indian Polity")
    chapter = Chapter.objects.create(subject=subject, name="Fundamental Rights")
    return Topic.objects.create(chapter=chapter, name="Right to Equality")


@pytest.mark.django_db
class TestQuestionIdentity:
    def test_question_creation_and_uuid(self):
        q = Question.objects.create()
        assert isinstance(q.id, uuid.UUID)
        assert q.created_at is not None
        assert q.updated_at is not None
        assert str(q) == f"Question {q.id}"

    def test_question_properties_helpers(self, topic):
        q = Question.objects.create()
        QuestionTopic.objects.create(question=q, topic=topic)
        assert q.published_version is None
        assert q.latest_version is None

        v1 = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Version 1 text",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        assert q.latest_version == v1

        v2 = QuestionVersion.objects.create(
            question=q,
            version_number=2,
            question_type=QuestionType.MCQ,
            text="Version 2 text",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v2, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v2, text="B", position=2, is_correct=False)
        transition_question_version_status(v2, QuestionStatus.REVIEW)
        transition_question_version_status(v2, QuestionStatus.APPROVED)
        transition_question_version_status(v2, QuestionStatus.PUBLISHED)

        assert q.latest_version == v2
        assert q.published_version == v2


@pytest.mark.django_db
class TestQuestionVersioningConstraints:
    def test_unique_version_number_per_question(self):
        q = Question.objects.create()
        QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="First version",
            difficulty=Difficulty.EASY,
        )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                QuestionVersion.objects.create(
                    question=q,
                    version_number=1,
                    question_type=QuestionType.MCQ,
                    text="Duplicate version number",
                    difficulty=Difficulty.EASY,
                )

    def test_same_version_number_allowed_for_different_questions(self):
        q1 = Question.objects.create()
        q2 = Question.objects.create()

        v1 = QuestionVersion.objects.create(
            question=q1,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Q1 V1",
            difficulty=Difficulty.EASY,
        )
        v2 = QuestionVersion.objects.create(
            question=q2,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Q2 V1",
            difficulty=Difficulty.EASY,
        )
        assert v1.version_number == 1
        assert v2.version_number == 1

    def test_positive_version_number_check(self):
        q = Question.objects.create()
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                QuestionVersion.objects.create(
                    question=q,
                    version_number=0,
                    question_type=QuestionType.MCQ,
                    text="Invalid version 0",
                    difficulty=Difficulty.EASY,
                )

    def test_only_one_published_version_per_question_constraint(self, topic):
        q = Question.objects.create()
        QuestionTopic.objects.create(question=q, topic=topic)
        v1 = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Published v1",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v1, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v1, text="B", position=2, is_correct=False)
        transition_question_version_status(v1, QuestionStatus.REVIEW)
        transition_question_version_status(v1, QuestionStatus.APPROVED)
        transition_question_version_status(v1, QuestionStatus.PUBLISHED)

        v2 = QuestionVersion.objects.create(
            question=q,
            version_number=2,
            question_type=QuestionType.MCQ,
            text="Published v2",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v2, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v2, text="B", position=2, is_correct=False)
        transition_question_version_status(v2, QuestionStatus.REVIEW)
        transition_question_version_status(v2, QuestionStatus.APPROVED)

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                transition_question_version_status(v2, QuestionStatus.PUBLISHED)

    def test_multiple_non_published_versions_can_coexist(self, topic):
        q = Question.objects.create()
        QuestionTopic.objects.create(question=q, topic=topic)
        v1 = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="v1 draft",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        v2 = QuestionVersion.objects.create(
            question=q,
            version_number=2,
            question_type=QuestionType.MCQ,
            text="v2 review",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
        )
        transition_question_version_status(v2, QuestionStatus.REVIEW)

        v3 = QuestionVersion.objects.create(
            question=q,
            version_number=3,
            question_type=QuestionType.MCQ,
            text="v3 published",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v3, text="A", position=1, is_correct=True)
        QuestionVersionChoice.objects.create(question_version=v3, text="B", position=2, is_correct=False)
        transition_question_version_status(v3, QuestionStatus.REVIEW)
        transition_question_version_status(v3, QuestionStatus.APPROVED)
        transition_question_version_status(v3, QuestionStatus.PUBLISHED)

        assert q.versions.count() == 3

    def test_question_cannot_be_deleted_if_version_exists(self):
        q = Question.objects.create()
        QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="v1 draft",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        with pytest.raises(ProtectedError):
            q.delete()


@pytest.mark.django_db
class TestQuestionTopicRelationship:
    def test_question_topic_association(self, topic):
        q = Question.objects.create()
        qt = QuestionTopic.objects.create(question=q, topic=topic)

        assert qt.question == q
        assert qt.topic == topic
        assert q.question_topics.count() == 1
        assert topic.question_topics.count() == 1

    def test_duplicate_question_topic_rejected(self, topic):
        q = Question.objects.create()
        QuestionTopic.objects.create(question=q, topic=topic)

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                QuestionTopic.objects.create(question=q, topic=topic)

    def test_learning_topic_deletion_is_protected_when_referenced(self, topic):
        q = Question.objects.create()
        QuestionTopic.objects.create(question=q, topic=topic)

        with pytest.raises(ProtectedError):
            topic.delete()


@pytest.mark.django_db
class TestContentTypeModels:
    def test_choices_model_and_constraints(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Sample MCQ",
            difficulty=Difficulty.EASY,
        )
        c1 = QuestionVersionChoice.objects.create(
            question_version=v,
            text="Option A",
            position=1,
            is_correct=True,
        )
        c2 = QuestionVersionChoice.objects.create(
            question_version=v,
            text="Option B",
            position=2,
            is_correct=False,
        )
        assert v.choices.count() == 2

        # Duplicate position under same version rejected
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                QuestionVersionChoice.objects.create(
                    question_version=v,
                    text="Duplicate Pos 1",
                    position=1,
                    is_correct=False,
                )

        # Non-positive position rejected
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                QuestionVersionChoice.objects.create(
                    question_version=v,
                    text="Pos 0",
                    position=0,
                    is_correct=False,
                )

    def test_true_false_content_model(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="Is the earth round?",
            difficulty=Difficulty.EASY,
        )
        tf = TrueFalseContent.objects.create(question_version=v, answer=True)
        assert tf.question_version == v
        assert tf.answer is True
        assert v.true_false_content == tf

    def test_assertion_reason_content_model(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.ASSERTION_REASON,
            text="Evaluate assertion and reason",
            difficulty=Difficulty.HARD,
        )
        ar = AssertionReasonContent.objects.create(
            question_version=v,
            assertion="Preamble is part of Constitution.",
            reason="Kesavananda Bharati case established this.",
            correct_relationship=AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
        )
        assert ar.correct_relationship == AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT
        assert v.assertion_reason_content == ar

    def test_match_following_models_and_constraints(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.MATCH_FOLLOWING,
            text="Match columns",
            difficulty=Difficulty.MEDIUM,
        )
        MatchFollowingContent.objects.create(question_version=v)

        l1 = MatchFollowingItem.objects.create(
            question_version=v, side=MatchItemSide.LEFT, text="Article 14", position=1
        )
        l2 = MatchFollowingItem.objects.create(
            question_version=v, side=MatchItemSide.LEFT, text="Article 21", position=2
        )
        r1 = MatchFollowingItem.objects.create(
            question_version=v, side=MatchItemSide.RIGHT, text="Equality before law", position=1
        )
        r2 = MatchFollowingItem.objects.create(
            question_version=v, side=MatchItemSide.RIGHT, text="Protection of life", position=2
        )

        p1 = MatchFollowingPair.objects.create(question_version=v, left_item=l1, right_item=r1)
        p2 = MatchFollowingPair.objects.create(question_version=v, left_item=l2, right_item=r2)

        assert v.match_items.count() == 4
        assert v.match_pairs.count() == 2

        # Duplicate side & position rejected
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                MatchFollowingItem.objects.create(
                    question_version=v, side=MatchItemSide.LEFT, text="Duplicate pos", position=1
                )

        # Duplicate left item in pairs rejected
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                MatchFollowingPair.objects.create(question_version=v, left_item=l1, right_item=r2)

        # Duplicate right item in pairs rejected
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                MatchFollowingPair.objects.create(question_version=v, left_item=l2, right_item=r1)

    def test_descriptive_content_model(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=QuestionType.DESCRIPTIVE,
            text="Discuss basic structure doctrine",
            difficulty=Difficulty.HARD,
        )
        desc = DescriptiveContent.objects.create(
            question_version=v,
            marks=10,
            expected_answer="Should mention Kesavananda Bharati case and core principles.",
        )
        assert desc.marks == 10
        assert v.descriptive_content == desc

        # Non-positive marks rejected
        q2 = Question.objects.create()
        v2 = QuestionVersion.objects.create(
            question=q2,
            version_number=1,
            question_type=QuestionType.DESCRIPTIVE,
            text="Discuss",
            difficulty=Difficulty.HARD,
        )
        with transaction.atomic():
            with pytest.raises((IntegrityError, ValidationError)):
                DescriptiveContent.objects.create(
                    question_version=v2,
                    marks=0,
                    expected_answer="Invalid marks",
                )


@pytest.mark.django_db
class TestMatchFollowingIntegrity:
    def test_left_item_from_version_a_cannot_be_paired_with_right_item_from_version_b(self):
        q = Question.objects.create()
        v_a = QuestionVersion.objects.create(
            question=q, version_number=1, question_type=QuestionType.MATCH_FOLLOWING, text="V1", difficulty=Difficulty.EASY
        )
        v_b = QuestionVersion.objects.create(
            question=q, version_number=2, question_type=QuestionType.MATCH_FOLLOWING, text="V2", difficulty=Difficulty.EASY
        )
        l_a = MatchFollowingItem.objects.create(question_version=v_a, side=MatchItemSide.LEFT, text="L_A", position=1)
        r_b = MatchFollowingItem.objects.create(question_version=v_b, side=MatchItemSide.RIGHT, text="R_B", position=1)

        with pytest.raises(ValidationError) as exc:
            MatchFollowingPair.objects.create(question_version=v_a, left_item=l_a, right_item=r_b)
        assert "right_item must belong to the same QuestionVersion as the pair" in str(exc.value)

    def test_right_item_from_version_a_cannot_be_paired_with_left_item_from_version_b(self):
        q = Question.objects.create()
        v_a = QuestionVersion.objects.create(
            question=q, version_number=1, question_type=QuestionType.MATCH_FOLLOWING, text="V1", difficulty=Difficulty.EASY
        )
        v_b = QuestionVersion.objects.create(
            question=q, version_number=2, question_type=QuestionType.MATCH_FOLLOWING, text="V2", difficulty=Difficulty.EASY
        )
        l_b = MatchFollowingItem.objects.create(question_version=v_b, side=MatchItemSide.LEFT, text="L_B", position=1)
        r_a = MatchFollowingItem.objects.create(question_version=v_a, side=MatchItemSide.RIGHT, text="R_A", position=1)

        with pytest.raises(ValidationError) as exc:
            MatchFollowingPair.objects.create(question_version=v_a, left_item=l_b, right_item=r_a)
        assert "left_item must belong to the same QuestionVersion as the pair" in str(exc.value)

    def test_valid_same_version_pairing_succeeds(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q, version_number=1, question_type=QuestionType.MATCH_FOLLOWING, text="V1", difficulty=Difficulty.EASY
        )
        l1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L1", position=1)
        r1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R1", position=1)
        p = MatchFollowingPair.objects.create(question_version=v, left_item=l1, right_item=r1)
        assert p.id is not None
        assert p.left_item == l1
        assert p.right_item == r1

    def test_item_sides_strictly_enforced_in_pair(self):
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q, version_number=1, question_type=QuestionType.MATCH_FOLLOWING, text="V1", difficulty=Difficulty.EASY
        )
        l1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L1", position=1)
        l2 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L2", position=2)
        r1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R1", position=1)

        # left_item side must be LEFT (passing right item fails)
        with pytest.raises(ValidationError) as exc:
            MatchFollowingPair.objects.create(question_version=v, left_item=r1, right_item=r1)
        assert "left_item must belong to the LEFT side" in str(exc.value)

        # right_item side must be RIGHT (passing left item fails)
        with pytest.raises(ValidationError) as exc:
            MatchFollowingPair.objects.create(question_version=v, left_item=l1, right_item=l2)
        assert "right_item must belong to the RIGHT side" in str(exc.value)
