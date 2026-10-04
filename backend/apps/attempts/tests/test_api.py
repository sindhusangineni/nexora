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
    AttemptResult,
    AttemptStatus,
    EvaluationState,
    ScoreFloorPolicy,
)
from apps.attempts.models.enums import AttemptResultStatus
from apps.question_bank.models import (
    Question,
    QuestionVersion,
    QuestionVersionChoice,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    user = User.objects.create_user(email="student@example.com", password="Password123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def other_student_user():
    user = User.objects.create_user(email="student2@example.com", password="Password123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_user():
    user = User.objects.create_user(email="admin@example.com", password="Password123!")
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser_only_user():
    return User.objects.create_superuser(
        email="superuser_only@example.com",
        password="Password123!",
    )


@pytest.mark.django_db
class TestAttemptsAPI:
    @pytest.fixture(autouse=True)
    def setup_data(self, student_user):
        # Create Assessment & Paper
        self.assessment = Assessment.objects.create(
            title="Attempts API Assessment",
            duration_seconds=3600,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
        )
        self.section = AssessmentSection.objects.create(
            assessment=self.assessment,
            title="General Knowledge",
            position=1,
        )
        self.paper = AssessmentPaper.objects.create(
            assessment=self.assessment,
            status=PaperStatus.GENERATED,
            duration_seconds=3600,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
        )

        # Question 1: MCQ
        self.q1 = Question.objects.create()
        self.v1 = QuestionVersion.objects.create(
            question=self.q1,
            version_number=1,
            question_type="MCQ",
            text="What is the capital of France?",
            explanation="Secret explanation that student must never see!",
            difficulty="EASY",
            status="DRAFT",
        )
        self.c1 = QuestionVersionChoice.objects.create(
            question_version=self.v1,
            text="Paris",
            position=1,
            is_correct=True,
        )
        self.c2 = QuestionVersionChoice.objects.create(
            question_version=self.v1,
            text="Berlin",
            position=2,
            is_correct=False,
        )
        QuestionVersion.objects.filter(id=self.v1.id).update(status="PUBLISHED")

        self.paper_item1 = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=self.q1.id,
            question_version_id=self.v1.id,
            presentation_order=1,
            allocated_marks=Decimal("2.0000"),
            allocated_penalty=Decimal("0.5000"),
        )

    def test_anonymous_requests_rejected_with_401(self, api_client):
        # Start attempt
        resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_can_start_attempt(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        assert resp.status_code == status.HTTP_201_CREATED

        data = resp.json()
        assert data["student_id"] == str(student_user.id)
        assert data["assessment_paper_id"] == str(self.paper.id)
        assert data["status"] == "IN_PROGRESS"
        assert len(data["items"]) == 1

        # Check delivery response safety: NO answer keys, explanations, or internal markings
        item = data["items"][0]
        assert "explanation" not in item
        assert "is_correct" not in item
        assert "correct_choice_ids" not in item
        assert len(item["choices"]) == 2
        for choice in item["choices"]:
            assert "is_correct" not in choice

    def test_get_active_attempt_delivery_safety_and_ownership(
        self, api_client, student_user, other_student_user, superadmin_user
    ):
        api_client.force_authenticate(user=student_user)
        create_resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        attempt_id = create_resp.json()["id"]

        # Owner student can get delivery
        resp = api_client.get(f"/api/v1/attempts/{attempt_id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == attempt_id

        # Other student is rejected (403)
        api_client.force_authenticate(user=other_student_user)
        resp_forbidden = api_client.get(f"/api/v1/attempts/{attempt_id}/")
        assert resp_forbidden.status_code == status.HTTP_403_FORBIDDEN

        # Superadmin can view delivery
        api_client.force_authenticate(user=superadmin_user)
        resp_admin = api_client.get(f"/api/v1/attempts/{attempt_id}/")
        assert resp_admin.status_code == status.HTTP_200_OK

    def test_save_and_clear_response(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        create_resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        attempt_id = create_resp.json()["id"]
        item_id = create_resp.json()["items"][0]["id"]

        # Save MCQ response
        resp = api_client.put(
            f"/api/v1/attempts/{attempt_id}/items/{item_id}/response/",
            {"question_type": "MCQ", "choice_id": str(self.c1.id)},
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["answer_state"] == "ANSWERED"
        assert str(self.c1.id) in data["selected_choice_ids"]

        # Clear response
        del_resp = api_client.delete(f"/api/v1/attempts/{attempt_id}/items/{item_id}/response/")
        assert del_resp.status_code == status.HTTP_200_OK
        del_data = del_resp.json()
        assert del_data["answer_state"] == "UNANSWERED"
        assert del_data["selected_choice_ids"] == []

    def test_submit_attempt_and_retrieve_result(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        create_resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        attempt_id = create_resp.json()["id"]
        item_id = create_resp.json()["items"][0]["id"]

        # Answer correctly
        api_client.put(
            f"/api/v1/attempts/{attempt_id}/items/{item_id}/response/",
            {"question_type": "MCQ", "choice_id": str(self.c1.id)},
        )

        # Submit attempt
        sub_resp = api_client.post(f"/api/v1/attempts/{attempt_id}/submit/")
        assert sub_resp.status_code == status.HTTP_200_OK
        assert sub_resp.json()["status"] == "EVALUATED"

        # Get result
        res_resp = api_client.get(f"/api/v1/attempts/{attempt_id}/result/")
        assert res_resp.status_code == status.HTTP_200_OK
        res_data = res_resp.json()
        assert res_data["status"] == "FINAL"
        assert res_data["score"] == "2.00"
        assert res_data["correct_questions"] == 1
        assert res_data["pending_evaluation_questions"] == 0

    def test_superadmin_descriptive_evaluation(self, api_client, student_user, superadmin_user, superuser_only_user):
        # Create descriptive question on paper
        q_desc = Question.objects.create()
        v_desc = QuestionVersion.objects.create(
            question=q_desc,
            version_number=1,
            question_type="DESCRIPTIVE",
            text="Explain gravity.",
            difficulty="MEDIUM",
            status="DRAFT",
        )
        QuestionVersion.objects.filter(id=v_desc.id).update(status="PUBLISHED")

        paper_item_desc = AssessmentPaperItem.objects.create(
            paper=self.paper,
            assessment_section=self.section,
            question_id=q_desc.id,
            question_version_id=v_desc.id,
            presentation_order=2,
            allocated_marks=Decimal("5.0000"),
            allocated_penalty=Decimal("0.0000"),
        )

        api_client.force_authenticate(user=student_user)
        create_resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        attempt_id = create_resp.json()["id"]
        desc_item_id = [i["id"] for i in create_resp.json()["items"] if i["paper_item_id"] == str(paper_item_desc.id)][0]

        # Student submits descriptive answer
        api_client.put(
            f"/api/v1/attempts/{attempt_id}/items/{desc_item_id}/response/",
            {"question_type": "DESCRIPTIVE", "text_response": "Gravity is spacetime curvature."},
        )
        sub_resp = api_client.post(f"/api/v1/attempts/{attempt_id}/submit/")
        assert sub_resp.json()["status"] == "SUBMITTED"

        # Student cannot evaluate (403)
        eval_resp = api_client.post(
            f"/api/v1/attempts/{attempt_id}/items/{desc_item_id}/evaluate/",
            {"evaluation_state": "CORRECT"},
        )
        assert eval_resp.status_code == status.HTTP_403_FORBIDDEN

        # Direct superuser without Superadmin group cannot evaluate (403)
        api_client.force_authenticate(user=superuser_only_user)
        eval_resp_su = api_client.post(
            f"/api/v1/attempts/{attempt_id}/items/{desc_item_id}/evaluate/",
            {"evaluation_state": "CORRECT"},
        )
        assert eval_resp_su.status_code == status.HTTP_403_FORBIDDEN

        # Superadmin evaluates
        api_client.force_authenticate(user=superadmin_user)
        eval_resp_admin = api_client.post(
            f"/api/v1/attempts/{attempt_id}/items/{desc_item_id}/evaluate/",
            {
                "evaluation_state": "PARTIALLY_CORRECT",
                "marks_awarded": "4.0000",
                "evaluation_comments": "Great answer, well articulated.",
            },
        )
        assert eval_resp_admin.status_code == status.HTTP_200_OK
        assert eval_resp_admin.json()["evaluation_state"] == "PARTIALLY_CORRECT"
        assert eval_resp_admin.json()["marks_awarded"] == "4.0000"

    def test_cancel_attempt_endpoint(self, api_client, student_user, superadmin_user, superuser_only_user):
        api_client.force_authenticate(user=student_user)
        create_resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        attempt_id = create_resp.json()["id"]

        # Student cannot cancel (403)
        cancel_resp = api_client.post(f"/api/v1/attempts/{attempt_id}/cancel/", {"reason": "Student cancel"})
        assert cancel_resp.status_code == status.HTTP_403_FORBIDDEN

        # Superuser only cannot cancel (403)
        api_client.force_authenticate(user=superuser_only_user)
        cancel_resp_su = api_client.post(f"/api/v1/attempts/{attempt_id}/cancel/", {"reason": "Superuser cancel"})
        assert cancel_resp_su.status_code == status.HTTP_403_FORBIDDEN

        # Superadmin cancels
        api_client.force_authenticate(user=superadmin_user)
        cancel_resp_admin = api_client.post(
            f"/api/v1/attempts/{attempt_id}/cancel/",
            {"reason": "Administrative disqualification"},
        )
        assert cancel_resp_admin.status_code == status.HTTP_200_OK
        data = cancel_resp_admin.json()
        assert data["status"] == "CANCELLED"
        assert data["cancellation_reason"] == "Administrative disqualification"

    def test_superadmin_review_endpoint(self, api_client, student_user, superadmin_user):
        api_client.force_authenticate(user=student_user)
        create_resp = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        attempt_id = create_resp.json()["id"]

        # Student cannot access review (403)
        resp = api_client.get(f"/api/v1/attempts/{attempt_id}/review/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Superadmin can review
        api_client.force_authenticate(user=superadmin_user)
        resp_admin = api_client.get(f"/api/v1/attempts/{attempt_id}/review/")
        assert resp_admin.status_code == status.HTTP_200_OK
        assert resp_admin.json()["id"] == attempt_id
        assert len(resp_admin.json()["items"]) == 1

    def test_attempt_history_authentication_required(self, api_client):
        resp = api_client.get("/api/v1/attempts/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_attempt_history_empty_structure(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        resp = api_client.get("/api/v1/attempts/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 0
        assert data["next"] is None
        assert data["previous"] is None
        assert data["results"] == []

    def test_attempt_history_student_isolation(self, api_client, student_user, other_student_user):
        # Create attempt for student 1
        api_client.force_authenticate(user=student_user)
        resp1 = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        assert resp1.status_code == status.HTTP_201_CREATED
        att1_id = resp1.json()["id"]

        # Create attempt for student 2 on self.paper (different student, same paper is valid)
        api_client.force_authenticate(user=other_student_user)
        resp2 = api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})
        assert resp2.status_code == status.HTTP_201_CREATED
        att2_id = resp2.json()["id"]

        # Student 1 only sees att1
        api_client.force_authenticate(user=student_user)
        h1 = api_client.get("/api/v1/attempts/").json()
        assert h1["count"] == 1
        assert h1["results"][0]["id"] == att1_id

        # Student 1 supplying query param ?student_id=other is ignored and still scoped
        h1_tampered = api_client.get(f"/api/v1/attempts/?student_id={other_student_user.id}").json()
        assert h1_tampered["count"] == 1
        assert h1_tampered["results"][0]["id"] == att1_id

        # Student 2 only sees att2
        api_client.force_authenticate(user=other_student_user)
        h2 = api_client.get("/api/v1/attempts/").json()
        assert h2["count"] == 1
        assert h2["results"][0]["id"] == att2_id

    def test_attempt_history_ordering_and_pagination(self, api_client, student_user):
        from datetime import timedelta
        base_time = datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)

        # Create 3 attempts manually for student
        for idx in range(3):
            att = Attempt.objects.create(
                student_id=student_user.id,
                assessment_paper_id=self.paper.id,
                attempt_number=idx + 1,
                status=AttemptStatus.IN_PROGRESS,
                duration_seconds=3600,
                started_at=base_time + timedelta(hours=idx),
                expires_at=base_time + timedelta(hours=idx, seconds=3600),
            )

        api_client.force_authenticate(user=student_user)
        resp = api_client.get("/api/v1/attempts/?page_size=2")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 3
        assert len(data["results"]) == 2
        assert data["next"] is not None

        # Verify newest started_at first
        first_attempt = data["results"][0]
        second_attempt = data["results"][1]
        assert first_attempt["attempt_number"] == 3
        assert second_attempt["attempt_number"] == 2

    def test_attempt_history_result_states_and_filtering(self, api_client, student_user):
        from datetime import timedelta
        base_time = datetime(2026, 10, 2, 10, 0, 0, tzinfo=timezone.utc)

        # 1. In-progress attempt without result
        att_active = Attempt.objects.create(
            student_id=student_user.id,
            assessment_paper_id=self.paper.id,
            attempt_number=1,
            status=AttemptStatus.IN_PROGRESS,
            duration_seconds=3600,
            started_at=base_time,
            expires_at=base_time + timedelta(hours=1),
        )

        # 2. Submitted attempt with PENDING result
        att_pending = Attempt.objects.create(
            student_id=student_user.id,
            assessment_paper_id=self.paper.id,
            attempt_number=2,
            status=AttemptStatus.SUBMITTED,
            duration_seconds=3600,
            started_at=base_time + timedelta(hours=1),
            expires_at=base_time + timedelta(hours=2),
            submitted_at=base_time + timedelta(hours=1, minutes=30),
            submission_reason="MANUAL",
        )
        AttemptResult.objects.create(
            attempt=att_pending,
            status=AttemptResultStatus.PENDING,
            maximum_score=Decimal("10.00"),
            total_questions=5,
            attempted_questions=4,
            correct_questions=2,
            incorrect_questions=2,
            partially_correct_questions=0,
            unanswered_questions=1,
            pending_evaluation_questions=0,
        )

        # 3. Evaluated attempt with FINAL result
        att_final = Attempt.objects.create(
            student_id=student_user.id,
            assessment_paper_id=self.paper.id,
            attempt_number=3,
            status=AttemptStatus.EVALUATED,
            duration_seconds=3600,
            started_at=base_time + timedelta(hours=2),
            expires_at=base_time + timedelta(hours=3),
            submitted_at=base_time + timedelta(hours=2, minutes=45),
            submission_reason="MANUAL",
        )
        AttemptResult.objects.create(
            attempt=att_final,
            status=AttemptResultStatus.FINAL,
            score=Decimal("8.00"),
            maximum_score=Decimal("10.00"),
            percentage=Decimal("80.00"),
            total_questions=5,
            attempted_questions=5,
            correct_questions=4,
            incorrect_questions=1,
            partially_correct_questions=0,
            unanswered_questions=0,
            pending_evaluation_questions=0,
            finalized_at=base_time + timedelta(hours=2, minutes=50),
        )

        api_client.force_authenticate(user=student_user)
        all_resp = api_client.get("/api/v1/attempts/").json()
        assert all_resp["count"] == 3

        # Check final attempt values
        final_item = next(r for r in all_resp["results"] if r["id"] == str(att_final.id))
        assert final_item["status"] == "EVALUATED"
        assert final_item["result_status"] == "FINAL"
        assert final_item["score"] == "8.00"
        assert final_item["maximum_score"] == "10.00"
        assert final_item["percentage"] == "80.00"
        assert final_item["total_questions"] == 5

        # Check pending attempt values
        pending_item = next(r for r in all_resp["results"] if r["id"] == str(att_pending.id))
        assert pending_item["status"] == "SUBMITTED"
        assert pending_item["result_status"] == "PENDING"
        assert pending_item["score"] is None
        assert pending_item["maximum_score"] == "10.00"
        assert pending_item["percentage"] is None

        # Check active attempt values
        active_item = next(r for r in all_resp["results"] if r["id"] == str(att_active.id))
        assert active_item["status"] == "IN_PROGRESS"
        assert active_item["result_status"] is None
        assert active_item["score"] is None

        # Test status filter: ?status=EVALUATED
        eval_only = api_client.get("/api/v1/attempts/?status=EVALUATED").json()
        assert eval_only["count"] == 1
        assert eval_only["results"][0]["id"] == str(att_final.id)

    def test_attempt_history_superadmin_access(self, api_client, student_user, superadmin_user):
        # Create attempt for student
        api_client.force_authenticate(user=student_user)
        api_client.post("/api/v1/attempts/", {"assessment_paper_id": str(self.paper.id)})

        # Superadmin accessing /attempts/ gets only their own attempts (0)
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.get("/api/v1/attempts/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 0
        assert data["results"] == []

