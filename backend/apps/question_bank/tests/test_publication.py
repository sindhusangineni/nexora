import pytest

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.exceptions import (
    ContentRepresentationError,
    PublicationValidationError,
)
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
from apps.question_bank.validators import (
    validate_single_content_representation,
    validate_version_for_publication,
)


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


def create_approved_version(question, version_number=1, **kwargs):
    kwargs.setdefault("status", QuestionStatus.DRAFT)
    v = QuestionVersion.objects.create(
        question=question,
        version_number=version_number,
        **kwargs,
    )
    transition_question_version_status(v, QuestionStatus.REVIEW)
    transition_question_version_status(v, QuestionStatus.APPROVED)
    return v


@pytest.mark.django_db
class TestCommonPublicationValidation:
    def test_empty_text_rejected_for_publication(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="   ",
            difficulty=Difficulty.EASY,
        )
        TrueFalseContent.objects.create(question_version=v, answer=True)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "Question text cannot be empty" in str(exc.value)

    def test_missing_topic_association_rejected_for_publication(self):
        q = Question.objects.create()  # No topic attached
        v = create_approved_version(
            question=q,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="Is water wet?",
            difficulty=Difficulty.EASY,
        )
        TrueFalseContent.objects.create(question_version=v, answer=True)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "associated with at least one Learning Topic" in str(exc.value)


@pytest.mark.django_db
class TestMCQPublicationValidation:
    def test_mcq_requires_at_least_two_choices(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Sample MCQ",
            difficulty=Difficulty.EASY,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="Only one choice", position=1, is_correct=True)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "at least 2 choices" in str(exc.value)

    def test_mcq_requires_exactly_one_correct_choice(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="Sample MCQ",
            difficulty=Difficulty.EASY,
        )
        # 0 correct choices
        c1 = QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=False)
        c2 = QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "exactly 1 correct choice" in str(exc.value)

        # 2 correct choices
        c1.is_correct = True
        c1.save()
        c2.is_correct = True
        c2.save()

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "exactly 1 correct choice" in str(exc.value)

        # 1 correct choice succeeds
        c2.is_correct = False
        c2.save()
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestMultipleSelectPublicationValidation:
    def test_multiple_select_requires_at_least_one_correct_choice(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MULTIPLE_SELECT,
            text="Sample Multi-select",
            difficulty=Difficulty.MEDIUM,
        )
        c1 = QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=False)
        c2 = QuestionVersionChoice.objects.create(question_version=v, text="B", position=2, is_correct=False)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "at least 1 correct choice" in str(exc.value)

        # Multiple correct choices succeed
        c1.is_correct = True
        c1.save()
        c2.is_correct = True
        c2.save()

        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestTrueFalsePublicationValidation:
    def test_true_false_missing_content_fails(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="Is 2+2=4?",
            difficulty=Difficulty.EASY,
        )
        with pytest.raises(PublicationValidationError) as exc:
            validate_version_for_publication(v)
        assert "require TrueFalseContent" in str(exc.value)

        with pytest.raises(ContentRepresentationError):
            transition_question_version_status(v, QuestionStatus.PUBLISHED)

    def test_true_false_valid_content_succeeds(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="Is 2+2=4?",
            difficulty=Difficulty.EASY,
        )
        TrueFalseContent.objects.create(question_version=v, answer=True)

        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestAssertionReasonPublicationValidation:
    def test_assertion_reason_missing_content_fails(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.ASSERTION_REASON,
            text="Assess statements",
            difficulty=Difficulty.HARD,
        )
        with pytest.raises(PublicationValidationError) as exc:
            validate_version_for_publication(v)
        assert "require AssertionReasonContent" in str(exc.value)

        with pytest.raises(ContentRepresentationError):
            transition_question_version_status(v, QuestionStatus.PUBLISHED)

    def test_assertion_reason_blank_fields_fail(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.ASSERTION_REASON,
            text="Assess statements",
            difficulty=Difficulty.HARD,
        )
        ar = AssertionReasonContent.objects.create(
            question_version=v,
            assertion="  ",
            reason="Valid reason",
            correct_relationship=AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
        )
        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "Assertion text cannot be empty" in str(exc.value)

        ar.assertion = "Valid assertion"
        ar.reason = "   "
        ar.save()
        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "Reason text cannot be empty" in str(exc.value)

    def test_assertion_reason_valid_content_succeeds(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.ASSERTION_REASON,
            text="Assess statements",
            difficulty=Difficulty.HARD,
        )
        AssertionReasonContent.objects.create(
            question_version=v,
            assertion="Fundamental rights are justiciable.",
            reason="Article 32 provides remedies.",
            correct_relationship=AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
        )
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestMatchFollowingPublicationValidation:
    def test_match_following_fewer_than_two_items_fails(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MATCH_FOLLOWING,
            text="Match following columns",
            difficulty=Difficulty.MEDIUM,
        )
        MatchFollowingContent.objects.create(question_version=v)
        l1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L1", position=1)
        r1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R1", position=1)
        MatchFollowingPair.objects.create(question_version=v, left_item=l1, right_item=r1)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "at least 2 LEFT items" in str(exc.value)

    def test_match_following_unequal_sides_fails(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MATCH_FOLLOWING,
            text="Match following columns",
            difficulty=Difficulty.MEDIUM,
        )
        MatchFollowingContent.objects.create(question_version=v)
        MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L1", position=1)
        MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L2", position=2)
        MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L3", position=3)
        MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R1", position=1)
        MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R2", position=2)

        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "count mismatch" in str(exc.value)

    def test_match_following_valid_content_succeeds(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MATCH_FOLLOWING,
            text="Match following columns",
            difficulty=Difficulty.MEDIUM,
        )
        MatchFollowingContent.objects.create(question_version=v)
        l1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L1", position=1)
        l2 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.LEFT, text="L2", position=2)
        r1 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R1", position=1)
        r2 = MatchFollowingItem.objects.create(question_version=v, side=MatchItemSide.RIGHT, text="R2", position=2)

        MatchFollowingPair.objects.create(question_version=v, left_item=l1, right_item=r2)
        MatchFollowingPair.objects.create(question_version=v, left_item=l2, right_item=r1)

        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestDescriptivePublicationValidation:
    def test_descriptive_missing_expected_answer_fails(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.DESCRIPTIVE,
            text="Explain fundamental rights",
            difficulty=Difficulty.HARD,
        )
        DescriptiveContent.objects.create(
            question_version=v,
            marks=10,
            expected_answer="   ",
        )
        with pytest.raises(PublicationValidationError) as exc:
            transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert "non-empty expected answer" in str(exc.value)

    def test_descriptive_valid_content_succeeds(self, question_with_topic):
        v = create_approved_version(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.DESCRIPTIVE,
            text="Explain fundamental rights",
            difficulty=Difficulty.HARD,
        )
        DescriptiveContent.objects.create(
            question_version=v,
            marks=10,
            expected_answer="Must discuss Articles 12-35 and judicial review.",
        )
        transition_question_version_status(v, QuestionStatus.PUBLISHED)
        assert v.status == QuestionStatus.PUBLISHED


@pytest.mark.django_db
class TestSingleContentRepresentationInvariant:
    def test_mcq_cannot_have_true_false_content(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="MCQ item",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        with pytest.raises(ContentRepresentationError) as exc:
            TrueFalseContent.objects.create(question_version=v, answer=True)
        assert "TrueFalseContent can only be associated with question_type 'TRUE_FALSE'" in str(exc.value)

    def test_true_false_cannot_have_choices(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="TF item",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        with pytest.raises(ContentRepresentationError) as exc:
            QuestionVersionChoice.objects.create(question_version=v, text="Choice", position=1)
        assert "QuestionVersionChoice can only be associated with MCQ or MULTIPLE_SELECT" in str(exc.value)

    def test_version_cannot_have_multiple_incompatible_content_representations(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="MCQ item",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="A", position=1, is_correct=True)
        # Directly insert TrueFalseContent into DB bypassing model save to simulate conflicting rows
        TrueFalseContent.objects.bulk_create([TrueFalseContent(question_version=v, answer=True)])

        with pytest.raises(ContentRepresentationError) as exc:
            validate_single_content_representation(v)
        assert "multiple incompatible content representations" in str(exc.value)

    def test_missing_required_type_representation_is_detected(self, question_with_topic):
        # MCQ with 0 choices
        v_mcq = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="MCQ with zero choices",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        with pytest.raises(ContentRepresentationError) as exc:
            validate_single_content_representation(v_mcq)
        assert "has no content representation" in str(exc.value)

        # TRUE_FALSE with no content
        v_tf = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=2,
            question_type=QuestionType.TRUE_FALSE,
            text="TF with zero content",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        with pytest.raises(ContentRepresentationError) as exc:
            validate_single_content_representation(v_tf)
        assert "has no content representation" in str(exc.value)

    def test_publication_validation_remains_separate_completeness_check(self, question_with_topic):
        v = QuestionVersion.objects.create(
            question=question_with_topic,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="MCQ with 1 choice",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(question_version=v, text="Only one choice", position=1, is_correct=True)

        # 1. Structurally valid: single content representation check passes
        validate_single_content_representation(v)

        # 2. Publication completeness check fails: MCQ requires >= 2 choices
        with pytest.raises(PublicationValidationError) as exc:
            validate_version_for_publication(v)
        assert "at least 2 choices" in str(exc.value)
