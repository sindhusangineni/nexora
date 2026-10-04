import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentSection,
    PaperStatus,
)
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptItemChoice,
    AttemptResponse,
    AttemptResponseChoice,
    AttemptResponseMatch,
    AttemptResult,
    AttemptSectionResult,
    AttemptStatus,
    EvaluationState,
    ScoreFloorPolicy,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.models import (
    AssertionReasonContent,
    DescriptiveContent,
    MatchFollowingContent,
    MatchFollowingItem,
    MatchFollowingPair,
    Question,
    QuestionTopic,
    QuestionVersion,
    QuestionVersionChoice,
    TrueFalseContent,
)
from apps.question_bank.models.enums import (
    AssertionReasonRelationship,
    Difficulty,
    MatchItemSide,
    QuestionStatus,
    QuestionType,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    user = User.objects.create_user(email="student_review@example.com", password="Password123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def other_student_user():
    user = User.objects.create_user(email="other_student@example.com", password="Password123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_user():
    user = User.objects.create_user(
        email="admin_review@example.com",
        password="Password123!",
        is_staff=True,
        is_superuser=True,
    )
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.mark.django_db
class TestResultsAndReview:
    @pytest.fixture(autouse=True)
    def setup_data(self, student_user, superadmin_user):
        self.now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)

        # 1. Setup Taxonomy
        self.domain = Domain.objects.create(name="Engineering")
        self.subject = Subject.objects.create(domain=self.domain, name="Computer Science")
        self.chapter = Chapter.objects.create(subject=self.subject, name="Algorithms")
        self.topic = Topic.objects.create(chapter=self.chapter, name="Sorting")

        # 2. Setup Assessment & Paper
        self.assessment = Assessment.objects.create(
            title="General CS Exam",
            duration_seconds=3600,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
        )
        self.section = AssessmentSection.objects.create(
            assessment=self.assessment,
            title="Core CS Section",
            position=1,
        )
        self.paper = AssessmentPaper.objects.create(
            assessment=self.assessment,
            status=PaperStatus.GENERATED,
            duration_seconds=3600,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
        )

        # 3. Create all 6 Question Types
        # A. MCQ
        self.q_mcq = Question.objects.create()
        QuestionTopic.objects.create(question=self.q_mcq, topic=self.topic)
        self.qv_mcq = QuestionVersion.objects.create(
            question=self.q_mcq,
            version_number=1,
            question_type=QuestionType.MCQ,
            text="What is the average time complexity of QuickSort?",
            explanation="QuickSort average complexity is O(N log N).",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
        )
        self.c1 = QuestionVersionChoice.objects.create(
            question_version=self.qv_mcq, text="O(N log N)", position=1, is_correct=True
        )
        self.c2 = QuestionVersionChoice.objects.create(
            question_version=self.qv_mcq, text="O(N^2)", position=2, is_correct=False
        )
        self.c3 = QuestionVersionChoice.objects.create(
            question_version=self.qv_mcq, text="O(N)", position=3, is_correct=False
        )

        # B. MULTIPLE_SELECT
        self.q_ms = Question.objects.create()
        self.qv_ms = QuestionVersion.objects.create(
            question=self.q_ms,
            version_number=1,
            question_type=QuestionType.MULTIPLE_SELECT,
            text="Which of the following are comparison-based sorts?",
            explanation="MergeSort and HeapSort compare elements.",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
        )
        self.ms_c1 = QuestionVersionChoice.objects.create(
            question_version=self.qv_ms, text="MergeSort", position=1, is_correct=True
        )
        self.ms_c2 = QuestionVersionChoice.objects.create(
            question_version=self.qv_ms, text="HeapSort", position=2, is_correct=True
        )
        self.ms_c3 = QuestionVersionChoice.objects.create(
            question_version=self.qv_ms, text="CountingSort", position=3, is_correct=False
        )

        # C. TRUE_FALSE
        self.q_tf = Question.objects.create()
        self.qv_tf = QuestionVersion.objects.create(
            question=self.q_tf,
            version_number=1,
            question_type=QuestionType.TRUE_FALSE,
            text="Binary Search requires a sorted array.",
            explanation="Binary search operates by halving sorted search spaces.",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        TrueFalseContent.objects.create(question_version=self.qv_tf, answer=True)

        # D. ASSERTION_REASON
        self.q_ar = Question.objects.create()
        self.qv_ar = QuestionVersion.objects.create(
            question=self.q_ar,
            version_number=1,
            question_type=QuestionType.ASSERTION_REASON,
            text="Evaluate the statements about Hash Tables.",
            explanation="Hash tables provide O(1) expected time due to good hash distribution.",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
        )
        AssertionReasonContent.objects.create(
            question_version=self.qv_ar,
            assertion="Hash tables offer O(1) average lookup time.",
            reason="Collisions are completely impossible in hash tables.",
            correct_relationship=AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE,
        )

        # E. MATCH_FOLLOWING
        self.q_mf = Question.objects.create()
        self.qv_mf = QuestionVersion.objects.create(
            question=self.q_mf,
            version_number=1,
            question_type=QuestionType.MATCH_FOLLOWING,
            text="Match the data structures with their properties.",
            explanation="Stack is LIFO, Queue is FIFO.",
            difficulty=Difficulty.EASY,
            status=QuestionStatus.DRAFT,
        )
        MatchFollowingContent.objects.create(question_version=self.qv_mf)
        self.left1 = MatchFollowingItem.objects.create(
            question_version=self.qv_mf, side=MatchItemSide.LEFT, text="Stack", position=1
        )
        self.left2 = MatchFollowingItem.objects.create(
            question_version=self.qv_mf, side=MatchItemSide.LEFT, text="Queue", position=2
        )
        self.right1 = MatchFollowingItem.objects.create(
            question_version=self.qv_mf, side=MatchItemSide.RIGHT, text="LIFO", position=1
        )
        self.right2 = MatchFollowingItem.objects.create(
            question_version=self.qv_mf, side=MatchItemSide.RIGHT, text="FIFO", position=2
        )
        MatchFollowingPair.objects.create(
            question_version=self.qv_mf, left_item=self.left1, right_item=self.right1
        )
        MatchFollowingPair.objects.create(
            question_version=self.qv_mf, left_item=self.left2, right_item=self.right2
        )

        # F. DESCRIPTIVE
        self.q_desc = Question.objects.create()
        self.qv_desc = QuestionVersion.objects.create(
            question=self.q_desc,
            version_number=1,
            question_type=QuestionType.DESCRIPTIVE,
            text="Explain Dijkstra's shortest path algorithm.",
            explanation="Dijkstra uses greedy choice and priority queue.",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
        )
        DescriptiveContent.objects.create(
            question_version=self.qv_desc,
            marks=10,
            expected_answer="Dijkstra finds single-source shortest paths in non-negative weighted graphs.",
        )

        QuestionVersion.objects.filter(
            id__in=[
                self.qv_mcq.id,
                self.qv_ms.id,
                self.qv_tf.id,
                self.qv_ar.id,
                self.qv_mf.id,
                self.qv_desc.id,
            ]
        ).update(status=QuestionStatus.PUBLISHED)

        # 4. AssessmentPaperItems
        self.pi_mcq = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q_mcq.id,
            question_version_id=self.qv_mcq.id,
            presentation_order=1,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.50"),
        )
        self.pi_ms = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q_ms.id,
            question_version_id=self.qv_ms.id,
            presentation_order=2,
            allocated_marks=Decimal("4.00"),
            allocated_penalty=Decimal("1.00"),
        )
        self.pi_tf = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q_tf.id,
            question_version_id=self.qv_tf.id,
            presentation_order=3,
            allocated_marks=Decimal("1.00"),
            allocated_penalty=Decimal("0.00"),
        )
        self.pi_ar = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q_ar.id,
            question_version_id=self.qv_ar.id,
            presentation_order=4,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.50"),
        )
        self.pi_mf = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q_mf.id,
            question_version_id=self.qv_mf.id,
            presentation_order=5,
            allocated_marks=Decimal("3.00"),
            allocated_penalty=Decimal("0.00"),
        )
        self.pi_desc = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q_desc.id,
            question_version_id=self.qv_desc.id,
            presentation_order=6,
            allocated_marks=Decimal("10.00"),
            allocated_penalty=Decimal("0.00"),
        )

    def _create_attempt_with_all_questions(self, student_user, status=AttemptStatus.SUBMITTED):
        attempt = Attempt.objects.create(
            student_id=student_user.id,
            assessment_paper_id=self.paper.id,
            attempt_number=1,
            duration_seconds=3600,
            score_floor_policy=ScoreFloorPolicy.ZERO_FLOOR_TOTAL,
            status=status,
            started_at=self.now,
            expires_at=datetime(2026, 10, 4, 13, 0, 0, tzinfo=timezone.utc),
            submitted_at=self.now if status != AttemptStatus.IN_PROGRESS else None,
            submission_reason="MANUAL" if status != AttemptStatus.IN_PROGRESS else None,
        )

        # Attempt items
        # 1. MCQ (answered correctly)
        ai_mcq = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=self.pi_mcq.id,
            assessment_section_id=self.section.id,
            question_id=self.q_mcq.id,
            question_version_id=self.qv_mcq.id,
            presentation_order=1,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.50"),
        )
        AttemptItemChoice.objects.create(attempt_item=ai_mcq, choice_id=self.c1.id, presented_position=1)
        AttemptItemChoice.objects.create(attempt_item=ai_mcq, choice_id=self.c2.id, presented_position=2)
        AttemptItemChoice.objects.create(attempt_item=ai_mcq, choice_id=self.c3.id, presented_position=3)
        resp_mcq = AttemptResponse.objects.create(attempt_item=ai_mcq, answer_state=AnswerState.ANSWERED)
        AttemptResponseChoice.objects.create(attempt_response=resp_mcq, choice_id=self.c1.id)
        AttemptEvaluation.objects.create(
            attempt_item=ai_mcq,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("2.00"),
            marks_deducted=Decimal("0.00"),
            net_marks=Decimal("2.00"),
            evaluated_at=self.now,
        )

        # 2. MULTIPLE_SELECT (answered correctly)
        ai_ms = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=self.pi_ms.id,
            assessment_section_id=self.section.id,
            question_id=self.q_ms.id,
            question_version_id=self.qv_ms.id,
            presentation_order=2,
            allocated_marks=Decimal("4.00"),
            allocated_penalty=Decimal("1.00"),
        )
        AttemptItemChoice.objects.create(attempt_item=ai_ms, choice_id=self.ms_c1.id, presented_position=1)
        AttemptItemChoice.objects.create(attempt_item=ai_ms, choice_id=self.ms_c2.id, presented_position=2)
        AttemptItemChoice.objects.create(attempt_item=ai_ms, choice_id=self.ms_c3.id, presented_position=3)
        resp_ms = AttemptResponse.objects.create(attempt_item=ai_ms, answer_state=AnswerState.ANSWERED)
        AttemptResponseChoice.objects.create(attempt_response=resp_ms, choice_id=self.ms_c1.id)
        AttemptResponseChoice.objects.create(attempt_response=resp_ms, choice_id=self.ms_c2.id)
        AttemptEvaluation.objects.create(
            attempt_item=ai_ms,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("4.00"),
            marks_deducted=Decimal("0.00"),
            net_marks=Decimal("4.00"),
            evaluated_at=self.now,
        )

        # 3. TRUE_FALSE (unanswered)
        ai_tf = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=self.pi_tf.id,
            assessment_section_id=self.section.id,
            question_id=self.q_tf.id,
            question_version_id=self.qv_tf.id,
            presentation_order=3,
            allocated_marks=Decimal("1.00"),
            allocated_penalty=Decimal("0.00"),
        )
        AttemptResponse.objects.create(attempt_item=ai_tf, answer_state=AnswerState.UNANSWERED)
        AttemptEvaluation.objects.create(
            attempt_item=ai_tf,
            evaluation_state=EvaluationState.UNATTEMPTED,
            marks_awarded=Decimal("0.00"),
            marks_deducted=Decimal("0.00"),
            net_marks=Decimal("0.00"),
        )

        # 4. ASSERTION_REASON (answered incorrectly)
        ai_ar = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=self.pi_ar.id,
            assessment_section_id=self.section.id,
            question_id=self.q_ar.id,
            question_version_id=self.qv_ar.id,
            presentation_order=4,
            allocated_marks=Decimal("2.00"),
            allocated_penalty=Decimal("0.50"),
        )
        resp_ar = AttemptResponse.objects.create(
            attempt_item=ai_ar,
            answer_state=AnswerState.ANSWERED,
            assertion_reason_response=AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
        )
        AttemptEvaluation.objects.create(
            attempt_item=ai_ar,
            evaluation_state=EvaluationState.INCORRECT,
            marks_awarded=Decimal("0.00"),
            marks_deducted=Decimal("0.50"),
            net_marks=Decimal("-0.50"),
            evaluated_at=self.now,
        )

        # 5. MATCH_FOLLOWING (answered correctly)
        ai_mf = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=self.pi_mf.id,
            assessment_section_id=self.section.id,
            question_id=self.q_mf.id,
            question_version_id=self.qv_mf.id,
            presentation_order=5,
            allocated_marks=Decimal("3.00"),
            allocated_penalty=Decimal("0.00"),
        )
        resp_mf = AttemptResponse.objects.create(attempt_item=ai_mf, answer_state=AnswerState.ANSWERED)
        AttemptResponseMatch.objects.create(attempt_response=resp_mf, left_item_id=self.left1.id, right_item_id=self.right1.id)
        AttemptResponseMatch.objects.create(attempt_response=resp_mf, left_item_id=self.left2.id, right_item_id=self.right2.id)
        AttemptEvaluation.objects.create(
            attempt_item=ai_mf,
            evaluation_state=EvaluationState.CORRECT,
            marks_awarded=Decimal("3.00"),
            marks_deducted=Decimal("0.00"),
            net_marks=Decimal("3.00"),
            evaluated_at=self.now,
        )

        # 6. DESCRIPTIVE (answered, pending evaluation)
        ai_desc = AttemptItem.objects.create(
            attempt=attempt,
            paper_item_id=self.pi_desc.id,
            assessment_section_id=self.section.id,
            question_id=self.q_desc.id,
            question_version_id=self.qv_desc.id,
            presentation_order=6,
            allocated_marks=Decimal("10.00"),
            allocated_penalty=Decimal("0.00"),
        )
        AttemptResponse.objects.create(
            attempt_item=ai_desc,
            answer_state=AnswerState.ANSWERED,
            text_response="Dijkstra algorithm uses a priority queue to iteratively pick min distance nodes.",
        )
        AttemptEvaluation.objects.create(
            attempt_item=ai_desc,
            evaluation_state=EvaluationState.PENDING_EVALUATION,
            marks_awarded=Decimal("0.00"),
            marks_deducted=Decimal("0.00"),
            net_marks=Decimal("0.00"),
        )

        return attempt, ai_desc

    def test_result_authorization_and_isolation(self, api_client, student_user, other_student_user, superadmin_user):
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.SUBMITTED)
        AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.PENDING,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("38.64"),
            total_questions=6,
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            unanswered_questions=1,
            pending_evaluation_questions=1,
        )

        # 1. Unauthenticated gets 401
        res_unauth = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

        # 2. Other student gets 403 Forbidden
        api_client.force_authenticate(user=other_student_user)
        res_other = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res_other.status_code == status.HTTP_403_FORBIDDEN

        # 3. Student owner gets 200 OK
        api_client.force_authenticate(user=student_user)
        res_owner = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res_owner.status_code == status.HTTP_200_OK
        data = res_owner.json()
        assert data["attempt_id"] == str(attempt.id)
        assert data["assessment_paper_id"] == str(self.paper.id)
        assert data["attempt_number"] == 1
        assert data["attempt_status"] == "SUBMITTED"
        assert data["result_status"] == "PENDING"
        assert data["pending_evaluation_questions"] == 1

        # 4. Superadmin gets 200 OK
        api_client.force_authenticate(user=superadmin_user)
        res_admin = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res_admin.status_code == status.HTTP_200_OK

    def test_in_progress_attempt_result_rejected(self, api_client, student_user):
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.IN_PROGRESS)
        api_client.force_authenticate(user=student_user)

        res = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_section_performance_in_result(self, api_client, student_user):
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.EVALUATED)
        res_obj = AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.FINAL,
            score=Decimal("18.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("84.09"),
            total_questions=6,
            attempted_questions=5,
            correct_questions=4,
            incorrect_questions=1,
            unanswered_questions=1,
            pending_evaluation_questions=0,
            finalized_at=self.now,
        )
        AttemptSectionResult.objects.create(
            attempt_result=res_obj,
            assessment_section_id=self.section.id,
            section_title_snapshot="Core CS Section",
            section_order_snapshot=1,
            score=Decimal("18.50"),
            maximum_score=Decimal("22.00"),
            attempted_questions=5,
            correct_questions=4,
            incorrect_questions=1,
            unanswered_questions=1,
            pending_evaluation_questions=0,
        )

        api_client.force_authenticate(user=student_user)
        res = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data["section_results"]) == 1
        sec = data["section_results"][0]
        assert sec["section_name"] == "Core CS Section"
        assert sec["section_title_snapshot"] == "Core CS Section"
        assert sec["question_count"] == 6
        assert sec["score"] == "18.50"
        assert sec["maximum_score"] == "22.00"
        assert sec["percentage"] == "84.09"
        assert sec["attempted_questions"] == 5
        assert sec["correct_questions"] == 4
        assert sec["incorrect_questions"] == 1
        assert sec["unanswered_questions"] == 1

    def test_review_security_boundary_pending_vs_final(self, api_client, student_user, superadmin_user):
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.SUBMITTED)
        AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.PENDING,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("38.64"),
            total_questions=6,
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            unanswered_questions=1,
            pending_evaluation_questions=1,
        )

        # Student accesses PENDING attempt review
        api_client.force_authenticate(user=student_user)
        res_pending = api_client.get(f"/api/v1/attempts/{attempt.id}/review/")
        assert res_pending.status_code == status.HTTP_200_OK
        data_pending = res_pending.json()
        assert data_pending["result_status"] == "PENDING"
        assert len(data_pending["items"]) == 6

        # Critical Security Boundary Checks:
        for item in data_pending["items"]:
            # Answer keys & explanations must be strictly withheld
            assert item["correct_answer"] is None
            assert item["explanation"] is None
            # Choices must NOT reveal is_correct
            if "choices" in item and item["choices"]:
                for c in item["choices"]:
                    assert "is_correct" not in c or c["is_correct"] is None
            # Student serializer must NEVER expose evaluator internals
            assert "evaluator_id" not in item
            assert "is_evaluable" not in item

        # Candidate responses must still be present
        mcq_item = next(it for it in data_pending["items"] if it["question_type"] == "MCQ")
        assert mcq_item["candidate_answer"]["selected_choice_id"] == str(self.c1.id)
        assert mcq_item["evaluation_status"] == "CORRECT"

        desc_item = next(it for it in data_pending["items"] if it["question_type"] == "DESCRIPTIVE")
        assert desc_item["evaluation_status"] == "PENDING_EVALUATION"
        assert desc_item["marks_awarded"] is None
        assert "Dijkstra" in desc_item["candidate_answer"]["text_response"]

        # Superadmin can view even in PENDING state and receives full solutions
        api_client.force_authenticate(user=superadmin_user)
        res_admin = api_client.get(f"/api/v1/attempts/{attempt.id}/review/")
        assert res_admin.status_code == status.HTTP_200_OK
        admin_data = res_admin.json()
        admin_mcq = next(it for it in admin_data["items"] if it["question_type"] == "MCQ")
        assert admin_mcq["correct_answer"]["correct_choice_id"] == str(self.c1.id)
        assert "O(N log N)" in admin_mcq["explanation"]
        admin_desc = next(it for it in admin_data["items"] if it["question_type"] == "DESCRIPTIVE")
        assert admin_desc["is_evaluable"] is True
        assert admin_desc["correct_answer"]["model_answer"] is not None

    def test_question_review_all_six_question_types_final(self, api_client, student_user):
        attempt, ai_desc = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.EVALUATED)
        # Finalize descriptive evaluation
        ev_desc = ai_desc.evaluation
        ev_desc.evaluation_state = EvaluationState.CORRECT
        ev_desc.marks_awarded = Decimal("10.00")
        ev_desc.marks_deducted = Decimal("0.00")
        ev_desc.net_marks = Decimal("10.00")
        ev_desc.evaluated_at = self.now
        ev_desc.save()

        AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.FINAL,
            score=Decimal("18.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("84.09"),
            total_questions=6,
            attempted_questions=5,
            correct_questions=4,
            incorrect_questions=1,
            unanswered_questions=1,
            pending_evaluation_questions=0,
            finalized_at=self.now,
        )

        api_client.force_authenticate(user=student_user)
        res = api_client.get(f"/api/v1/attempts/{attempt.id}/review/")
        assert res.status_code == status.HTTP_200_OK
        items = res.json()["items"]
        assert len(items) == 6

        # 1. MCQ Review
        mcq = next(it for it in items if it["question_type"] == "MCQ")
        assert mcq["question_number"] == 1
        assert mcq["section_name"] == "Core CS Section"
        assert mcq["taxonomy"]["domain"] == "Engineering"
        assert mcq["taxonomy"]["subject"] == "Computer Science"
        assert mcq["candidate_answer"]["selected_choice_id"] == str(self.c1.id)
        assert mcq["correct_answer"]["correct_choice_id"] == str(self.c1.id)
        assert mcq["evaluation_status"] == "CORRECT"
        assert Decimal(mcq["marks_awarded"]) == Decimal("2.00")
        assert "QuickSort" in mcq["explanation"]

        # 2. MULTIPLE_SELECT Review
        ms = next(it for it in items if it["question_type"] == "MULTIPLE_SELECT")
        assert ms["question_number"] == 2
        assert set(ms["candidate_answer"]["selected_choice_ids"]) == {str(self.ms_c1.id), str(self.ms_c2.id)}
        assert set(ms["correct_answer"]["correct_choice_ids"]) == {str(self.ms_c1.id), str(self.ms_c2.id)}
        assert ms["evaluation_status"] == "CORRECT"
        assert Decimal(ms["marks_awarded"]) == Decimal("4.00")

        # 3. TRUE_FALSE Review (Unanswered)
        tf = next(it for it in items if it["question_type"] == "TRUE_FALSE")
        assert tf["question_number"] == 3
        assert tf["is_answered"] is False
        assert tf["answer_state"] == "UNANSWERED"
        assert tf["candidate_answer"]["boolean_response"] is None
        assert tf["correct_answer"]["correct_boolean"] is True
        assert tf["evaluation_status"] == "UNATTEMPTED"
        assert Decimal(tf["marks_awarded"]) == Decimal("0.00")

        # 4. ASSERTION_REASON Review (Incorrect)
        ar = next(it for it in items if it["question_type"] == "ASSERTION_REASON")
        assert ar["question_number"] == 4
        assert ar["assertion"] == "Hash tables offer O(1) average lookup time."
        assert ar["reason"] == "Collisions are completely impossible in hash tables."
        assert ar["candidate_answer"]["assertion_reason_response"] == AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT
        assert ar["correct_answer"]["correct_relationship"] == AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE
        assert ar["evaluation_status"] == "INCORRECT"

        # 5. MATCH_FOLLOWING Review
        mf = next(it for it in items if it["question_type"] == "MATCH_FOLLOWING")
        assert mf["question_number"] == 5
        assert len(mf["left_items"]) == 2
        assert len(mf["right_items"]) == 2
        assert len(mf["candidate_answer"]["matches"]) == 2
        assert len(mf["correct_answer"]["correct_matches"]) == 2
        assert mf["evaluation_status"] == "CORRECT"
        assert Decimal(mf["marks_awarded"]) == Decimal("3.00")

        # 6. DESCRIPTIVE Review
        desc = next(it for it in items if it["question_type"] == "DESCRIPTIVE")
        assert desc["question_number"] == 6
        assert "Dijkstra" in desc["candidate_answer"]["text_response"]
        assert "non-negative" in desc["correct_answer"]["model_answer"]
        assert desc["evaluation_status"] == "CORRECT"
        assert Decimal(desc["marks_awarded"]) == Decimal("10.00")
        assert "priority queue" in desc["explanation"]

    def test_manual_descriptive_evaluation_workflow(self, api_client, student_user, superadmin_user):
        attempt, ai_desc = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.SUBMITTED)
        AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.PENDING,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("38.64"),
            total_questions=6,
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            unanswered_questions=1,
            pending_evaluation_questions=1,
        )

        eval_url = f"/api/v1/attempts/{attempt.id}/items/{ai_desc.id}/evaluate/"

        # 1. Student cannot evaluate (403)
        api_client.force_authenticate(user=student_user)
        res_stu = api_client.post(eval_url, {"evaluation_state": "CORRECT", "marks_awarded": "10.00"})
        assert res_stu.status_code == status.HTTP_403_FORBIDDEN

        # 2. Superadmin marks validation: cannot exceed allocated marks
        api_client.force_authenticate(user=superadmin_user)
        res_invalid = api_client.post(eval_url, {"evaluation_state": "CORRECT", "marks_awarded": "15.00"})
        assert res_invalid.status_code == status.HTTP_400_BAD_REQUEST

        # 3. Superadmin PARTIALLY_CORRECT validation: must be strictly between 0 and 10
        res_part_inv = api_client.post(eval_url, {"evaluation_state": "PARTIALLY_CORRECT", "marks_awarded": "10.00"})
        assert res_part_inv.status_code == status.HTTP_400_BAD_REQUEST

        # 4. Superadmin evaluates PARTIALLY_CORRECT with 7.50 marks
        res_eval = api_client.post(
            eval_url,
            {
                "evaluation_state": "PARTIALLY_CORRECT",
                "marks_awarded": "7.50",
                "evaluation_comments": "Well explained but missed priority queue complexity analysis.",
            },
        )
        assert res_eval.status_code == status.HTTP_200_OK
        eval_data = res_eval.json()
        assert eval_data["evaluation_state"] == "PARTIALLY_CORRECT"
        assert Decimal(eval_data["marks_awarded"]) == Decimal("7.50")
        assert eval_data["evaluation_comments"] == "Well explained but missed priority queue complexity analysis."

        # 5. Verify Attempt transitions to EVALUATED and AttemptResult transitions to FINAL
        attempt.refresh_from_db()
        assert attempt.status == AttemptStatus.EVALUATED
        res_db = attempt.result
        assert res_db.status == AttemptResultStatus.FINAL
        assert res_db.pending_evaluation_questions == 0
        assert res_db.finalized_at is not None
        assert res_db.score == Decimal("16.00")  # 8.50 + 7.50

        # 6. Cannot evaluate again once finalized (400)
        res_re_eval = api_client.post(eval_url, {"evaluation_state": "CORRECT", "marks_awarded": "10.00"})
        assert res_re_eval.status_code == status.HTTP_400_BAD_REQUEST

    def test_historical_immutability(self, api_client, student_user):
        """Verifies review uses pinned QuestionVersion and version-owned child rows rather than newly created V2 versions."""
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.EVALUATED)
        AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.FINAL,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("38.64"),
            total_questions=6,
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            unanswered_questions=2,
            pending_evaluation_questions=0,
            finalized_at=self.now,
        )

        # 1. Archive V1 and create V2 for MCQ with completely different choices and correct answer
        QuestionVersion.objects.filter(id=self.qv_mcq.id).update(status=QuestionStatus.ARCHIVED)
        v2_mcq = QuestionVersion.objects.create(
            question=self.q_mcq,
            version_number=2,
            question_type=QuestionType.MCQ,
            text="MODIFIED QUESTION TEXT IN V2",
            explanation="MODIFIED EXPLANATION V2",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
        )
        QuestionVersionChoice.objects.create(
            question_version=v2_mcq, text="V2 Choice Alpha", position=1, is_correct=False
        )
        c_v2_correct = QuestionVersionChoice.objects.create(
            question_version=v2_mcq, text="V2 Choice Beta (Correct)", position=2, is_correct=True
        )
        QuestionVersion.objects.filter(id=v2_mcq.id).update(status=QuestionStatus.PUBLISHED)

        # 2. Archive V1 and create V2 for MATCH_FOLLOWING with new items and different pairings
        QuestionVersion.objects.filter(id=self.qv_mf.id).update(status=QuestionStatus.ARCHIVED)
        v2_mf = QuestionVersion.objects.create(
            question=self.q_mf,
            version_number=2,
            question_type=QuestionType.MATCH_FOLLOWING,
            text="V2 Match Graph Algorithms",
            explanation="V2 Explanation: Prim vs Kruskal.",
            difficulty=Difficulty.MEDIUM,
            status=QuestionStatus.DRAFT,
        )
        MatchFollowingContent.objects.create(question_version=v2_mf)
        mf_l1 = MatchFollowingItem.objects.create(
            question_version=v2_mf, side=MatchItemSide.LEFT, text="Kruskal", position=1
        )
        mf_l2 = MatchFollowingItem.objects.create(
            question_version=v2_mf, side=MatchItemSide.LEFT, text="Prim", position=2
        )
        mf_r1 = MatchFollowingItem.objects.create(
            question_version=v2_mf, side=MatchItemSide.RIGHT, text="Disjoint Set", position=1
        )
        mf_r2 = MatchFollowingItem.objects.create(
            question_version=v2_mf, side=MatchItemSide.RIGHT, text="Priority Queue", position=2
        )
        MatchFollowingPair.objects.create(
            question_version=v2_mf, left_item=mf_l1, right_item=mf_r1
        )
        MatchFollowingPair.objects.create(
            question_version=v2_mf, left_item=mf_l2, right_item=mf_r2
        )
        QuestionVersion.objects.filter(id=v2_mf.id).update(status=QuestionStatus.PUBLISHED)

        # 3. Archive V1 and create V2 for DESCRIPTIVE with new rubric and expected answer
        QuestionVersion.objects.filter(id=self.qv_desc.id).update(status=QuestionStatus.ARCHIVED)
        v2_desc = QuestionVersion.objects.create(
            question=self.q_desc,
            version_number=2,
            question_type=QuestionType.DESCRIPTIVE,
            text="Explain Floyd-Warshall Algorithm.",
            explanation="V2 Explanation: Dynamic programming all-pairs shortest path.",
            difficulty=Difficulty.HARD,
            status=QuestionStatus.DRAFT,
        )
        DescriptiveContent.objects.create(
            question_version=v2_desc,
            marks=15,
            expected_answer="Floyd-Warshall computes all-pairs shortest paths using dynamic programming in O(V^3).",
        )
        QuestionVersion.objects.filter(id=v2_desc.id).update(status=QuestionStatus.PUBLISHED)

        # 4. Request Review for the completed attempt pinned to V1
        api_client.force_authenticate(user=student_user)
        res = api_client.get(f"/api/v1/attempts/{attempt.id}/review/")
        assert res.status_code == status.HTTP_200_OK
        review_data = res.json()
        items = review_data["items"]

        # A. MCQ must still return immutable V1 text, explanation, choices, and correct answer
        mcq_item = next(it for it in items if it["question_type"] == "MCQ")
        assert mcq_item["question_text"] == "What is the average time complexity of QuickSort?"
        assert mcq_item["explanation"] == "QuickSort average complexity is O(N log N)."
        mcq_choice_texts = [c["text"] for c in mcq_item["choices"]]
        assert "O(N log N)" in mcq_choice_texts
        assert "V2 Choice Alpha" not in mcq_choice_texts
        assert "V2 Choice Beta (Correct)" not in mcq_choice_texts
        assert mcq_item["correct_answer"]["correct_choice_id"] == str(self.c1.id)
        assert mcq_item["correct_answer"]["correct_choice_id"] != str(c_v2_correct.id)

        # B. MATCH_FOLLOWING must still return immutable V1 left/right items and pairings
        mf_item = next(it for it in items if it["question_type"] == "MATCH_FOLLOWING")
        assert mf_item["question_text"] == "Match the data structures with their properties."
        assert mf_item["explanation"] == "Stack is LIFO, Queue is FIFO."
        left_texts = [li["text"] for li in mf_item["left_items"]]
        assert "Stack" in left_texts
        assert "Queue" in left_texts
        assert "Kruskal" not in left_texts
        assert "Prim" not in left_texts
        correct_pairs = mf_item["correct_answer"]["correct_matches"]
        assert len(correct_pairs) == 2
        assert any(p["left_item_id"] == str(self.left1.id) and p["right_item_id"] == str(self.right1.id) for p in correct_pairs)

        # C. DESCRIPTIVE must still return immutable V1 expected answer and explanation
        desc_item = next(it for it in items if it["question_type"] == "DESCRIPTIVE")
        assert desc_item["question_text"] == "Explain Dijkstra's shortest path algorithm."
        assert desc_item["explanation"] == "Dijkstra uses greedy choice and priority queue."
        assert desc_item["correct_answer"]["model_answer"] == "Dijkstra finds single-source shortest paths in non-negative weighted graphs."
        assert "Floyd-Warshall" not in desc_item["correct_answer"]["model_answer"]

    def test_historical_taxonomy_live_resolution(self, api_client, student_user):
        """
        Verifies that taxonomy context reflects live Domain/Topic labels rather than a frozen snapshot.
        If taxonomy entities are renamed, historical review reflects the updated live names.
        """
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.EVALUATED)
        AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.FINAL,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("38.64"),
            total_questions=6,
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            unanswered_questions=2,
            pending_evaluation_questions=0,
            finalized_at=self.now,
        )

        # Rename Domain and Topic in the live database after the attempt
        self.domain.name = "Renamed Engineering Domain"
        self.domain.save()
        self.topic.name = "Advanced QuickSort Topic"
        self.topic.save()

        api_client.force_authenticate(user=student_user)
        res = api_client.get(f"/api/v1/attempts/{attempt.id}/review/")
        assert res.status_code == status.HTTP_200_OK
        mcq_item = next(it for it in res.json()["items"] if it["question_type"] == "MCQ")

        # Proves taxonomy is resolved live from Topic -> Chapter -> Subject -> Domain
        assert mcq_item["taxonomy"]["domain"] == "Renamed Engineering Domain"
        assert mcq_item["taxonomy"]["topic"] == "Advanced QuickSort Topic"

    def test_historical_section_name_persistence(self, api_client, student_user):
        """
        Verifies that section_name in Result and Review is backed by the frozen AttemptSectionResult
        section_title_snapshot and does not change if the original AssessmentSection title changes.
        """
        attempt, _ = self._create_attempt_with_all_questions(student_user, status=AttemptStatus.EVALUATED)
        res_obj = AttemptResult.objects.create(
            attempt=attempt,
            status=AttemptResultStatus.FINAL,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            percentage=Decimal("38.64"),
            total_questions=6,
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            unanswered_questions=2,
            pending_evaluation_questions=0,
            finalized_at=self.now,
        )
        sec_result = AttemptSectionResult.objects.create(
            attempt_result=res_obj,
            assessment_section_id=self.section.id,
            section_title_snapshot="Original Frozen Section 1",
            section_order_snapshot=1,
            score=Decimal("8.50"),
            maximum_score=Decimal("22.00"),
            attempted_questions=4,
            correct_questions=3,
            incorrect_questions=1,
            partially_correct_questions=0,
            unanswered_questions=2,
            pending_evaluation_questions=0,
        )

        api_client.force_authenticate(user=student_user)

        # 1. Result API exposes the frozen snapshot as section_name
        res_result = api_client.get(f"/api/v1/attempts/{attempt.id}/result/")
        assert res_result.status_code == status.HTTP_200_OK
        sec_data = res_result.json()["section_results"][0]
        assert sec_data["section_name"] == "Original Frozen Section 1"
        assert sec_data["section_title_snapshot"] == "Original Frozen Section 1"

        # 2. Review API uses the frozen AttemptSectionResult snapshot for section_name
        res_review = api_client.get(f"/api/v1/attempts/{attempt.id}/review/")
        assert res_review.status_code == status.HTTP_200_OK
        item_sec_name = res_review.json()["items"][0]["section_name"]
        assert item_sec_name == "Original Frozen Section 1"

