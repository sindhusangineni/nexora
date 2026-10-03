import uuid
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
    AssessmentStatus,
    PaperStatus,
    ScopeType,
    SelectionRule,
)
from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.models import Question, QuestionTopic, QuestionVersion

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    user = User.objects.create_user(email="student@example.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_user():
    user = User.objects.create_user(email="admin@example.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser_only_user():
    return User.objects.create_superuser(
        email="superuser_only@example.com",
        password="StrongPassword123!",
    )


@pytest.mark.django_db
class TestAssessmentAPI:
    def test_anonymous_requests_rejected_with_401(self, api_client):
        # List assessments
        resp = api_client.get("/api/v1/assessment/assessments/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

        # Create assessment
        resp = api_client.post("/api/v1/assessment/assessments/", {"title": "Test"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    def test_superuser_without_group_rejected_for_writes(self, api_client, superuser_only_user):
        api_client.force_authenticate(user=superuser_only_user)
        resp = api_client.post("/api/v1/assessment/assessments/", {
            "title": "Superuser Attempt",
            "duration_seconds": 3600,
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_student_sees_only_published_assessments(self, api_client, student_user, superadmin_user):
        draft = Assessment.objects.create(title="Draft Assessment", status=AssessmentStatus.DRAFT)
        pub = Assessment.objects.create(title="Published Assessment", status=AssessmentStatus.PUBLISHED)

        # As Student
        api_client.force_authenticate(user=student_user)
        resp = api_client.get("/api/v1/assessment/assessments/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(pub.id)

        # Retrieve draft as student returns 404
        resp_draft = api_client.get(f"/api/v1/assessment/assessments/{draft.id}/")
        assert resp_draft.status_code == status.HTTP_404_NOT_FOUND

        # Retrieve published as student succeeds
        resp_pub = api_client.get(f"/api/v1/assessment/assessments/{pub.id}/")
        assert resp_pub.status_code == status.HTTP_200_OK

        # As Superadmin
        api_client.force_authenticate(user=superadmin_user)
        admin_resp = api_client.get("/api/v1/assessment/assessments/")
        assert admin_resp.status_code == status.HTTP_200_OK
        assert len(admin_resp.json()) == 2

    def test_superadmin_creates_and_updates_assessment(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.post("/api/v1/assessment/assessments/", {
            "title": "GS Prelims 2026",
            "description": "Mock Test 1",
            "type": "MOCK",
            "duration_seconds": 7200,
            "marks_per_question": "2.00",
            "penalty_per_question": "0.66",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assessment_id = resp.json()["id"]
        assert resp.json()["status"] == "DRAFT"

        # Update while DRAFT
        patch_resp = api_client.patch(f"/api/v1/assessment/assessments/{assessment_id}/", {
            "title": "GS Prelims 2026 Updated",
        })
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()["title"] == "GS Prelims 2026 Updated"

    def test_sections_crud(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        assessment = Assessment.objects.create(title="Section API Test")

        # Create section
        resp = api_client.post(f"/api/v1/assessment/assessments/{assessment.id}/sections/", {
            "title": "Polity",
            "description": "Constitutional provisions",
            "position": 1,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        sec_id = resp.json()["id"]

        # List sections
        list_resp = api_client.get(f"/api/v1/assessment/assessments/{assessment.id}/sections/")
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.json()) == 1

        # Delete section
        del_resp = api_client.delete(f"/api/v1/assessment/sections/{sec_id}/")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    def test_selection_rules_crud(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        assessment = Assessment.objects.create(title="Rule API Test")
        scope_uuid = uuid.uuid4()

        # Create rule
        resp = api_client.post(f"/api/v1/assessment/assessments/{assessment.id}/rules/", {
            "scope_type": "TOPIC",
            "scope_id": str(scope_uuid),
            "question_type": "MCQ",
            "difficulty": "MEDIUM",
            "question_count": 5,
            "position": 1,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        rule_id = resp.json()["id"]

        # List rules
        list_resp = api_client.get(f"/api/v1/assessment/assessments/{assessment.id}/rules/")
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.json()) == 1

        # Delete rule
        del_resp = api_client.delete(f"/api/v1/assessment/rules/{rule_id}/")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    def test_publish_and_archive_endpoints(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        assessment = Assessment.objects.create(title="Lifecycle API Test")
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=uuid.uuid4(),
            question_count=5,
            position=1,
        )

        # Publish
        pub_resp = api_client.post(f"/api/v1/assessment/assessments/{assessment.id}/publish/")
        assert pub_resp.status_code == status.HTTP_200_OK
        assert pub_resp.json()["status"] == "PUBLISHED"

        # Archive
        arch_resp = api_client.post(f"/api/v1/assessment/assessments/{assessment.id}/archive/")
        assert arch_resp.status_code == status.HTTP_200_OK
        assert arch_resp.json()["status"] == "ARCHIVED"

    def test_generate_paper_and_retrieve_endpoints(self, api_client, superadmin_user, student_user):
        # Set up learning and question bank entities
        domain = Domain.objects.create(name="Science")
        subject = Subject.objects.create(domain=domain, name="Physics")
        chapter = Chapter.objects.create(subject=subject, name="Mechanics")
        topic = Topic.objects.create(chapter=chapter, name="Kinematics")

        q1 = Question.objects.create()
        QuestionTopic.objects.create(question=q1, topic=topic)
        v1 = QuestionVersion.objects.create(
            question=q1,
            version_number=1,
            question_type="MCQ",
            difficulty="EASY",
            text="What is velocity?",
            status="DRAFT",
        )
        QuestionVersion.objects.filter(pk=v1.pk).update(status="PUBLISHED")
        v1.refresh_from_db()

        assessment = Assessment.objects.create(
            title="Physics Test",
            duration_seconds=1800,
            marks_per_question=Decimal("2.00"),
            penalty_per_question=Decimal("0.50"),
        )
        SelectionRule.objects.create(
            assessment=assessment,
            scope_type=ScopeType.TOPIC,
            scope_id=topic.id,
            question_count=1,
            position=1,
        )
        assessment.publish()

        # Generate paper as Student
        api_client.force_authenticate(user=student_user)
        gen_resp = api_client.post(f"/api/v1/assessment/assessments/{assessment.id}/generate-paper/")
        assert gen_resp.status_code == status.HTTP_201_CREATED
        paper_id = gen_resp.json()["id"]
        assert gen_resp.json()["duration_seconds"] == 1800
        assert gen_resp.json()["marks_per_question"] == "2.00"
        assert len(gen_resp.json()["items"]) == 1
        assert gen_resp.json()["items"][0]["question_id"] == str(q1.id)
        assert gen_resp.json()["items"][0]["question_version_id"] == str(v1.id)

        # Retrieve paper as Student
        get_resp = api_client.get(f"/api/v1/assessment/papers/{paper_id}/")
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.json()["id"] == paper_id
