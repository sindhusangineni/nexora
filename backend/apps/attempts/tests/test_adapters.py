import uuid
from decimal import Decimal
import pytest
from django.apps import apps

from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentSection,
    PaperStatus,
)
from apps.attempts.adapters.assessment import AssessmentPaperDeliveryAdapter
from apps.attempts.adapters.question_bank import DatabaseQuestionBankAnswerKeyAdapter
from apps.attempts.ports.assessment import DeliveryPayloadDTO
from apps.attempts.ports.question_bank import ObjectiveAnswerKeyDTO


@pytest.mark.django_db
class TestQuestionBankAnswerKeyAdapter:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        Question = apps.get_model("question_bank", "Question")
        QuestionVersion = apps.get_model("question_bank", "QuestionVersion")
        QuestionVersionChoice = apps.get_model("question_bank", "QuestionVersionChoice")
        TrueFalseContent = apps.get_model("question_bank", "TrueFalseContent")
        AssertionReasonContent = apps.get_model("question_bank", "AssertionReasonContent")
        MatchFollowingPair = apps.get_model("question_bank", "MatchFollowingPair")

        # 1. MCQ Question
        self.q_mcq = Question.objects.create()
        self.v_mcq = QuestionVersion.objects.create(
            question=self.q_mcq,
            version_number=1,
            question_type="MCQ",
            text="MCQ question text?",
            difficulty="EASY",
            status="DRAFT",
        )
        self.c1 = QuestionVersionChoice.objects.create(
            question_version=self.v_mcq,
            text="Correct choice",
            position=1,
            is_correct=True,
        )
        self.c2 = QuestionVersionChoice.objects.create(
            question_version=self.v_mcq,
            text="Incorrect choice",
            position=2,
            is_correct=False,
        )

        # 2. MULTIPLE_SELECT Question
        self.q_ms = Question.objects.create()
        self.v_ms = QuestionVersion.objects.create(
            question=self.q_ms,
            version_number=1,
            question_type="MULTIPLE_SELECT",
            text="Multiple select text?",
            difficulty="MEDIUM",
            status="DRAFT",
        )
        self.ms_c1 = QuestionVersionChoice.objects.create(
            question_version=self.v_ms,
            text="Correct 1",
            position=1,
            is_correct=True,
        )
        self.ms_c2 = QuestionVersionChoice.objects.create(
            question_version=self.v_ms,
            text="Incorrect",
            position=2,
            is_correct=False,
        )
        self.ms_c3 = QuestionVersionChoice.objects.create(
            question_version=self.v_ms,
            text="Correct 2",
            position=3,
            is_correct=True,
        )

        # 3. TRUE_FALSE Question
        self.q_tf = Question.objects.create()
        self.v_tf = QuestionVersion.objects.create(
            question=self.q_tf,
            version_number=1,
            question_type="TRUE_FALSE",
            text="The sky is blue.",
            difficulty="EASY",
            status="DRAFT",
        )
        TrueFalseContent.objects.create(
            question_version=self.v_tf,
            answer=True,
        )

        # 4. ASSERTION_REASON Question
        self.q_ar = Question.objects.create()
        self.v_ar = QuestionVersion.objects.create(
            question=self.q_ar,
            version_number=1,
            question_type="ASSERTION_REASON",
            text="Assertion and reason text",
            difficulty="HARD",
            status="DRAFT",
        )
        AssertionReasonContent.objects.create(
            question_version=self.v_ar,
            assertion="Assertion statement",
            reason="Reason statement",
            correct_relationship="BOTH_TRUE_REASON_CORRECT",
        )

        # 5. MATCH_FOLLOWING Question
        MatchFollowingItem = apps.get_model("question_bank", "MatchFollowingItem")
        self.q_mf = Question.objects.create()
        self.v_mf = QuestionVersion.objects.create(
            question=self.q_mf,
            version_number=1,
            question_type="MATCH_FOLLOWING",
            text="Match the following columns",
            difficulty="MEDIUM",
            status="DRAFT",
        )
        self.left_item_1 = MatchFollowingItem.objects.create(
            question_version=self.v_mf,
            side="LEFT",
            text="Left 1",
            position=1,
        )
        self.right_item_1 = MatchFollowingItem.objects.create(
            question_version=self.v_mf,
            side="RIGHT",
            text="Right 1",
            position=1,
        )
        self.left_item_2 = MatchFollowingItem.objects.create(
            question_version=self.v_mf,
            side="LEFT",
            text="Left 2",
            position=2,
        )
        self.right_item_2 = MatchFollowingItem.objects.create(
            question_version=self.v_mf,
            side="RIGHT",
            text="Right 2",
            position=2,
        )
        MatchFollowingPair.objects.create(
            question_version=self.v_mf,
            left_item=self.left_item_1,
            right_item=self.right_item_1,
        )
        MatchFollowingPair.objects.create(
            question_version=self.v_mf,
            left_item=self.left_item_2,
            right_item=self.right_item_2,
        )

        # 6. DESCRIPTIVE Question
        self.q_desc = Question.objects.create()
        self.v_desc = QuestionVersion.objects.create(
            question=self.q_desc,
            version_number=1,
            question_type="DESCRIPTIVE",
            text="Explain quantum entanglement.",
            difficulty="HARD",
            status="DRAFT",
        )

        # Set all to PUBLISHED
        QuestionVersion.objects.filter(
            id__in=[
                self.v_mcq.id,
                self.v_ms.id,
                self.v_tf.id,
                self.v_ar.id,
                self.v_mf.id,
                self.v_desc.id,
            ]
        ).update(status="PUBLISHED")

        self.adapter = DatabaseQuestionBankAnswerKeyAdapter()

    def test_mcq_answer_key_retrieval(self):
        keys = self.adapter.get_objective_answer_keys([self.v_mcq.id])
        assert self.v_mcq.id in keys
        dto = keys[self.v_mcq.id]
        assert isinstance(dto, ObjectiveAnswerKeyDTO)
        assert dto.question_type == "MCQ"
        assert dto.correct_choice_ids == {self.c1.id}
        assert dto.correct_boolean is None
        assert dto.correct_assertion_reason is None

    def test_multiple_select_answer_key_retrieval(self):
        keys = self.adapter.get_objective_answer_keys([self.v_ms.id])
        dto = keys[self.v_ms.id]
        assert dto.question_type == "MULTIPLE_SELECT"
        assert dto.correct_choice_ids == {self.ms_c1.id, self.ms_c3.id}

    def test_true_false_answer_key_retrieval(self):
        keys = self.adapter.get_objective_answer_keys([self.v_tf.id])
        dto = keys[self.v_tf.id]
        assert dto.question_type == "TRUE_FALSE"
        assert dto.correct_boolean is True
        assert dto.correct_choice_ids == set()

    def test_assertion_reason_answer_key_retrieval(self):
        keys = self.adapter.get_objective_answer_keys([self.v_ar.id])
        dto = keys[self.v_ar.id]
        assert dto.question_type == "ASSERTION_REASON"
        assert dto.correct_assertion_reason == "BOTH_TRUE_REASON_CORRECT"

    def test_match_following_answer_key_retrieval(self):
        keys = self.adapter.get_objective_answer_keys([self.v_mf.id])
        dto = keys[self.v_mf.id]
        assert dto.question_type == "MATCH_FOLLOWING"
        assert dto.correct_match_pairs == {
            self.left_item_1.id: self.right_item_1.id,
            self.left_item_2.id: self.right_item_2.id,
        }

    def test_descriptive_key_retrieval(self):
        keys = self.adapter.get_objective_answer_keys([self.v_desc.id])
        dto = keys[self.v_desc.id]
        assert dto.question_type == "DESCRIPTIVE"
        assert dto.correct_choice_ids == set()
        assert dto.correct_boolean is None
        assert dto.correct_assertion_reason is None
        assert dto.correct_match_pairs == {}

    def test_batch_all_question_types(self):
        all_ids = [
            self.v_mcq.id,
            self.v_ms.id,
            self.v_tf.id,
            self.v_ar.id,
            self.v_mf.id,
            self.v_desc.id,
        ]
        keys = self.adapter.get_objective_answer_keys(all_ids)
        assert len(keys) == 6
        for vid in all_ids:
            assert vid in keys

    def test_missing_version_handling(self):
        random_id = uuid.uuid4()
        keys = self.adapter.get_objective_answer_keys([random_id])
        assert keys == {}

    def test_empty_list_returns_empty_dict(self):
        keys = self.adapter.get_objective_answer_keys([])
        assert keys == {}


@pytest.mark.django_db
class TestAssessmentPaperDeliveryAdapterWiring:
    def test_assessment_paper_delivery_adapter(self):
        assessment = Assessment.objects.create(
            title="Attempts Delivery Paper",
            duration_seconds=1800,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
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

        Question = apps.get_model("question_bank", "Question")
        QuestionVersion = apps.get_model("question_bank", "QuestionVersion")
        QuestionVersionChoice = apps.get_model("question_bank", "QuestionVersionChoice")

        q1 = Question.objects.create()
        v1 = QuestionVersion.objects.create(
            question=q1,
            version_number=1,
            question_type="MCQ",
            text="MCQ Question for Delivery",
            difficulty="EASY",
            status="DRAFT",
        )
        c1 = QuestionVersionChoice.objects.create(
            question_version=v1,
            text="Choice A",
            position=1,
            is_correct=True,
        )
        QuestionVersion.objects.filter(id=v1.id).update(status="PUBLISHED")

        AssessmentPaperItem.objects.create(
            paper=paper,
            assessment_section=sec,
            question_id=q1.id,
            question_version_id=v1.id,
            presentation_order=1,
            allocated_marks=Decimal("2.0000"),
            allocated_penalty=Decimal("0.5000"),
        )

        adapter = AssessmentPaperDeliveryAdapter()
        student_id = uuid.uuid4()
        payload = adapter.get_paper_delivery_payload(paper.id, student_id)

        assert isinstance(payload, DeliveryPayloadDTO)
        assert payload.is_eligible is True
        assert payload.assessment_paper_id == paper.id
        assert payload.duration_seconds == 1800
        assert len(payload.items) == 1
        item = payload.items[0]
        assert item.question_id == q1.id
        assert item.question_version_id == v1.id
        assert item.presentation_order == 1
        assert item.allocated_marks == Decimal("2.0000")
        assert item.allocated_penalty == Decimal("0.5000")
        assert len(item.choices) == 1
        assert item.choices[0].choice_id == c1.id
