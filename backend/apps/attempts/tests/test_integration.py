import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.assessment.adapters.question_bank import DatabaseQuestionBankCandidateAdapter
from apps.assessment.application.generate_paper import generate_paper
from apps.assessment.models import (
    Assessment,
    AssessmentPaper,
    AssessmentPaperItem,
    AssessmentSection,
    AssessmentStatus,
    PaperStatus,
    ScopeType,
    SelectionRule,
)
from apps.attempts.application import (
    clear_response,
    evaluate_descriptive_item,
    save_response,
    start_attempt,
    submit_attempt,
)
from apps.attempts.authorization import AuthorizationContext
from apps.attempts.exceptions import AttemptExpired
from apps.attempts.models import (
    AnswerState,
    Attempt,
    AttemptEvaluation,
    AttemptItem,
    AttemptResult,
    AttemptSectionResult,
    AttemptStatus,
    EvaluationState,
    ScoreFloorPolicy,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.attempts.services.scoring import get_scoring_policy
from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.models import (
    AssertionReasonContent,
    MatchFollowingPair,
    Question,
    QuestionTopic,
    QuestionVersion,
    QuestionVersionChoice,
    TrueFalseContent,
)

User = get_user_model()


@pytest.mark.django_db
class TestEndToEndCoreAssessmentFlow:
    @pytest.fixture(autouse=True)
    def setup_base(self):
        self.t0 = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
        self.student = User.objects.create_user(email="learner@example.com", password="Password123!")
        student_group, _ = Group.objects.get_or_create(name="Student")
        self.student.groups.add(student_group)

        self.superadmin = User.objects.create_user(email="chief_admin@example.com", password="Password123!")
        admin_group, _ = Group.objects.get_or_create(name="Superadmin")
        self.superadmin.groups.add(admin_group)

        self.student_auth = AuthorizationContext(
            actor_id=self.student.id,
            is_student=True,
            is_superadmin=False,
        )
        self.superadmin_auth = AuthorizationContext(
            actor_id=self.superadmin.id,
            is_student=False,
            is_superadmin=True,
        )

        # Learning taxonomy
        self.domain = Domain.objects.create(name="Science & Technology")
        self.subject = Subject.objects.create(domain=self.domain, name="Physics")
        self.chapter = Chapter.objects.create(subject=self.subject, name="Electromagnetism")
        self.topic = Topic.objects.create(chapter=self.chapter, name="Magnetic Fields")

    def test_objective_only_assessment_flow_to_final_result(self):
        """
        Flow 1: Objective-only assessment
        Create/publish assessment -> generate paper -> start attempt -> receive delivery -> answer -> submit -> FINAL result.
        """
        # 1. Question Bank questions: 1 MCQ + 1 True/False
        q1 = Question.objects.create()
        v1 = QuestionVersion.objects.create(
            question=q1,
            version_number=1,
            question_type="MCQ",
            text="Which particle has positive charge?",
            difficulty="EASY",
            status="DRAFT",
        )
        c1 = QuestionVersionChoice.objects.create(question_version=v1, text="Proton", position=1, is_correct=True)
        c2 = QuestionVersionChoice.objects.create(question_version=v1, text="Electron", position=2, is_correct=False)
        QuestionVersion.objects.filter(id=v1.id).update(status="PUBLISHED")
        QuestionTopic.objects.create(question=q1, topic_id=self.topic.id)

        q2 = Question.objects.create()
        v2 = QuestionVersion.objects.create(
            question=q2,
            version_number=1,
            question_type="TRUE_FALSE",
            text="Magnetic field lines never intersect.",
            difficulty="EASY",
            status="DRAFT",
        )
        TrueFalseContent.objects.create(question_version=v2, answer=True)
        QuestionVersion.objects.filter(id=v2.id).update(status="PUBLISHED")
        QuestionTopic.objects.create(question=q2, topic_id=self.topic.id)

        # 2. Assessment definition
        assessment = Assessment.objects.create(
            title="Physics Objective Quiz",
            duration_seconds=1800,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
            status=AssessmentStatus.DRAFT,
        )
        sec = AssessmentSection.objects.create(
            assessment=assessment,
            title="Electromagnetism Section",
            position=1,
        )
        SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=sec,
            scope_type=ScopeType.TOPIC,
            scope_id=self.topic.id,
            question_count=2,
            position=1,
        )
        Assessment.objects.filter(id=assessment.id).update(status=AssessmentStatus.PUBLISHED)

        # 3. Paper Generation
        paper = generate_paper(
            assessment_id=assessment.id,
            question_bank_port=DatabaseQuestionBankCandidateAdapter(),
        )
        assert paper.status == PaperStatus.GENERATED
        assert paper.items.count() == 2

        # 4. Student starts attempt
        attempt = start_attempt(
            student_id=self.student.id,
            paper_id=paper.id,
            authorization_context=self.student_auth,
            now=self.t0,
        )
        assert attempt.status == AttemptStatus.IN_PROGRESS
        assert attempt.items.count() == 2

        # 5. Student answers questions
        item_mcq = attempt.items.get(question_version_id=v1.id)
        item_tf = attempt.items.get(question_version_id=v2.id)

        # Answer MCQ correctly
        save_response(
            attempt_id=attempt.id,
            attempt_item_id=item_mcq.id,
            authorization=self.student_auth,
            response_data={"question_type": "MCQ", "choice_id": c1.id},
            scoring_policy=get_scoring_policy(attempt.score_floor_policy),
            now=self.t0 + timedelta(minutes=2),
        )

        # Answer True/False correctly
        save_response(
            attempt_id=attempt.id,
            attempt_item_id=item_tf.id,
            authorization=self.student_auth,
            response_data={"question_type": "TRUE_FALSE", "boolean_response": True},
            scoring_policy=get_scoring_policy(attempt.score_floor_policy),
            now=self.t0 + timedelta(minutes=4),
        )

        # 6. Student submits attempt
        submitted_attempt, _ = submit_attempt(
            attempt_id=attempt.id,
            authorization=self.student_auth,
            scoring_policy=get_scoring_policy(attempt.score_floor_policy),
            now=self.t0 + timedelta(minutes=10),
        )

        # 7. Verification: Objective-only transitions immediately to EVALUATED and FINAL!
        assert submitted_attempt.status == AttemptStatus.EVALUATED
        result = AttemptResult.objects.get(attempt=submitted_attempt)
        assert result.status == AttemptResultStatus.FINAL
        assert result.finalized_at == self.t0 + timedelta(minutes=10)
        assert result.score == Decimal("4.00")
        assert result.maximum_score == Decimal("4.00")
        assert result.percentage == Decimal("100.00")
        assert result.correct_questions == 2
        assert result.incorrect_questions == 0
        assert result.pending_evaluation_questions == 0

    def test_descriptive_assessment_flow_with_superadmin_evaluation(self):
        """
        Flow 2: Descriptive assessment
        Create/publish assessment -> generate paper -> start attempt -> submit
        -> PENDING result -> Superadmin evaluates -> FINAL result.
        """
        # Question 1: Descriptive
        q_desc = Question.objects.create()
        v_desc = QuestionVersion.objects.create(
            question=q_desc,
            version_number=1,
            question_type="DESCRIPTIVE",
            text="Explain Maxwell's equations and their physical significance.",
            difficulty="HARD",
            status="DRAFT",
        )
        QuestionVersion.objects.filter(id=v_desc.id).update(status="PUBLISHED")
        QuestionTopic.objects.create(question=q_desc, topic_id=self.topic.id)

        assessment = Assessment.objects.create(
            title="Advanced Physics Exam",
            duration_seconds=3600,
            marks_per_question=Decimal("10.00"),
            penalty_per_question=Decimal("0.00"),
            status=AssessmentStatus.DRAFT,
        )
        sec = AssessmentSection.objects.create(
            assessment=assessment,
            title="Theory Section",
            position=1,
        )
        SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=sec,
            scope_type=ScopeType.TOPIC,
            scope_id=self.topic.id,
            question_count=1,
            position=1,
        )
        Assessment.objects.filter(id=assessment.id).update(status=AssessmentStatus.PUBLISHED)

        paper = generate_paper(
            assessment_id=assessment.id,
            question_bank_port=DatabaseQuestionBankCandidateAdapter(),
        )

        # Start attempt
        attempt = start_attempt(
            student_id=self.student.id,
            paper_id=paper.id,
            authorization_context=self.student_auth,
            now=self.t0,
        )
        item = attempt.items.first()

        # Submit descriptive answer
        save_response(
            attempt_id=attempt.id,
            attempt_item_id=item.id,
            authorization=self.student_auth,
            response_data={
                "question_type": "DESCRIPTIVE",
                "text_response": "Gauss's law, Gauss's law for magnetism, Faraday's law, and Ampere-Maxwell law.",
            },
            scoring_policy=get_scoring_policy(attempt.score_floor_policy),
            now=self.t0 + timedelta(minutes=20),
        )

        # Submit
        submitted_attempt, _ = submit_attempt(
            attempt_id=attempt.id,
            authorization=self.student_auth,
            scoring_policy=get_scoring_policy(attempt.score_floor_policy),
            now=self.t0 + timedelta(minutes=30),
        )

        # Because descriptive item requires human grading, attempt is SUBMITTED and result is PENDING!
        assert submitted_attempt.status == AttemptStatus.SUBMITTED
        result = AttemptResult.objects.get(attempt=submitted_attempt)
        assert result.status == AttemptResultStatus.PENDING
        assert result.finalized_at is None
        assert result.pending_evaluation_questions == 1
        assert result.score == Decimal("0.00")

        # Superadmin evaluates item
        eval_time = self.t0 + timedelta(hours=2)
        evaluated_attempt, _, evaluation, final_result = evaluate_descriptive_item(
            attempt_id=submitted_attempt.id,
            attempt_item_id=item.id,
            evaluation_state="PARTIALLY_CORRECT",
            marks_awarded=Decimal("8.5000"),
            evaluation_comments="Very good explanation of all 4 equations.",
            authorization=self.superadmin_auth,
            scoring_policy=get_scoring_policy(submitted_attempt.score_floor_policy),
            now=eval_time,
        )

        # Now all items evaluated: Attempt -> EVALUATED, AttemptResult -> FINAL
        assert evaluated_attempt.status == AttemptStatus.EVALUATED
        assert final_result.status == AttemptResultStatus.FINAL
        assert final_result.finalized_at == eval_time
        assert final_result.score == Decimal("8.50")
        assert final_result.maximum_score == Decimal("10.00")
        assert final_result.percentage == Decimal("85.00")
        assert final_result.pending_evaluation_questions == 0
        assert final_result.partially_correct_questions == 1

    def test_expired_attempt_timeout_flow(self):
        """
        Flow 3: Expired attempt
        Start -> expire -> mutation attempt -> timeout submission -> persisted timeout state.
        """
        q = Question.objects.create()
        v = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type="TRUE_FALSE",
            text="True or False?",
            difficulty="EASY",
            status="DRAFT",
        )
        TrueFalseContent.objects.create(question_version=v, answer=True)
        QuestionVersion.objects.filter(id=v.id).update(status="PUBLISHED")
        QuestionTopic.objects.create(question=q, topic_id=self.topic.id)

        assessment = Assessment.objects.create(
            title="Timed Assessment",
            duration_seconds=600,  # 10 minutes
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
            status=AssessmentStatus.DRAFT,
        )
        sec = AssessmentSection.objects.create(assessment=assessment, title="Sec", position=1)
        SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=sec,
            scope_type=ScopeType.TOPIC,
            scope_id=self.topic.id,
            question_count=1,
            position=1,
        )
        Assessment.objects.filter(id=assessment.id).update(status=AssessmentStatus.PUBLISHED)
        paper = generate_paper(
            assessment_id=assessment.id,
            question_bank_port=DatabaseQuestionBankCandidateAdapter(),
        )

        attempt = start_attempt(
            student_id=self.student.id,
            paper_id=paper.id,
            authorization_context=self.student_auth,
            now=self.t0,
        )
        item = attempt.items.first()

        # Try to save response after expiry (15 minutes later, duration was 10 minutes)
        expired_time = self.t0 + timedelta(minutes=15)
        with pytest.raises(AttemptExpired):
            save_response(
                attempt_id=attempt.id,
                attempt_item_id=item.id,
                authorization=self.student_auth,
                response_data={"question_type": "TRUE_FALSE", "boolean_response": True},
                scoring_policy=get_scoring_policy(attempt.score_floor_policy),
                now=expired_time,
            )

        # Verify auto-submission was committed durably
        attempt.refresh_from_db()
        assert attempt.status == AttemptStatus.EVALUATED
        assert attempt.submission_reason == "TIMEOUT"
        assert attempt.submitted_at == expired_time

        result = AttemptResult.objects.get(attempt=attempt)
        assert result.status == AttemptResultStatus.FINAL
        assert result.unanswered_questions == 1
        assert result.score == Decimal("0.00")
