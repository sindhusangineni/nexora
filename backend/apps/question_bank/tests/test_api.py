import uuid
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.application import create_question
from apps.question_bank.models import (
    AssertionReasonRelationship,
    Difficulty,
    Question,
    QuestionSourceType,
    QuestionStatus,
    QuestionType,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    user = User.objects.create_user(email="student@nexora.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Student")
    user.groups.add(group)
    return user


@pytest.fixture
def superadmin_user():
    user = User.objects.create_user(email="superadmin@nexora.com", password="StrongPassword123!")
    group, _ = Group.objects.get_or_create(name="Superadmin")
    user.groups.add(group)
    return user


@pytest.fixture
def superuser_only_user():
    return User.objects.create_superuser(
        email="superuser_only@nexora.com",
        password="StrongPassword123!",
    )


@pytest.fixture
def topic():
    domain = Domain.objects.create(name="Civil Services Exam")
    subject = Subject.objects.create(domain=domain, name="Indian Polity")
    chapter = Chapter.objects.create(subject=subject, name="Fundamental Rights")
    return Topic.objects.create(chapter=chapter, name="Right to Equality")


@pytest.mark.django_db
class TestQuestionBankAPIAuthenticationAndRBAC:
    def test_anonymous_requests_rejected_with_401(self, api_client):
        # List
        resp = api_client.get("/api/v1/question-bank/questions/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

        # Create
        resp = api_client.post("/api/v1/question-bank/questions/", {"text": "Test"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    def test_superuser_without_superadmin_group_rejected_for_writes(self, api_client, superuser_only_user):
        """is_superuser is NOT an application-role bypass for write mutations."""
        api_client.force_authenticate(user=superuser_only_user)
        resp = api_client.post("/api/v1/question-bank/questions/", {"text": "Test"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_student_cannot_create_questions(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        resp = api_client.post("/api/v1/question-bank/questions/", {"text": "Test"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_student_cannot_create_versions(self, api_client, student_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Q",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        api_client.force_authenticate(user=student_user)
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/", {"text": "V2"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_student_cannot_call_lifecycle_endpoints(self, api_client, student_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Q",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=student_user)
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/submit-review/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.django_db
class TestQuestionCreationAPI:
    @pytest.mark.parametrize(
        "q_type,content_payload",
        [
            (
                "MCQ",
                {
                    "choices": [
                        {"text": "Option 1", "position": 1, "is_correct": True},
                        {"text": "Option 2", "position": 2, "is_correct": False},
                    ]
                },
            ),
            (
                "MULTIPLE_SELECT",
                {
                    "choices": [
                        {"text": "Choice A", "position": 1, "is_correct": True},
                        {"text": "Choice B", "position": 2, "is_correct": True},
                    ]
                },
            ),
            (
                "TRUE_FALSE",
                {"true_false": {"answer": True}},
            ),
            (
                "ASSERTION_REASON",
                {
                    "assertion_reason": {
                        "assertion": "A statement",
                        "reason": "R statement",
                        "correct_relationship": AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
                    }
                },
            ),
            (
                "MATCH_FOLLOWING",
                {
                    "match_following": {
                        "left_items": [{"text": "L1", "position": 1}, {"text": "L2", "position": 2}],
                        "right_items": [{"text": "R1", "position": 1}, {"text": "R2", "position": 2}],
                        "pairs": [{"left_position": 1, "right_position": 2}, {"left_position": 2, "right_position": 1}],
                    }
                },
            ),
            (
                "DESCRIPTIVE",
                {"descriptive": {"marks": 15, "expected_answer": "Complete answer rubric"}},
            ),
        ],
    )
    def test_superadmin_can_create_all_six_question_types(
        self, api_client, superadmin_user, topic, q_type, content_payload
    ):
        api_client.force_authenticate(user=superadmin_user)
        payload = {
            "text": f"Question text for {q_type}",
            "question_type": q_type,
            "difficulty": "MEDIUM",
            "explanation": "Explanation text",
            "topic_ids": [str(topic.id)],
            "source_type": "ORIGINAL",
            "source_name": "Nexora Authors",
            **content_payload,
        }
        resp = api_client.post("/api/v1/question-bank/questions/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "id" in data
        assert str(topic.id) in data["topic_ids"]
        assert data["latest_version"]["version_number"] == 1
        assert data["latest_version"]["status"] == "DRAFT"
        assert data["latest_version"]["question_type"] == q_type
        assert data["latest_version"]["source_type"] == "ORIGINAL"
        assert data["latest_version"]["source_name"] == "Nexora Authors"

    def test_create_question_with_provenance_metadata(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)
        payload = {
            "text": "UPSC Question 2024",
            "question_type": "MCQ",
            "difficulty": "HARD",
            "topic_ids": [str(topic.id)],
            "source_type": "UPSC_PREVIOUS_YEAR",
            "source_name": "UPSC CSE 2024",
            "source_reference": "GS Paper 1 Q42",
            "source_year": 2024,
            "external_question_id": "UPSC-2024-Q42",
            "choices": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": False},
            ],
        }
        resp = api_client.post("/api/v1/question-bank/questions/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        v = resp.json()["latest_version"]
        assert v["source_type"] == "UPSC_PREVIOUS_YEAR"
        assert v["source_name"] == "UPSC CSE 2024"
        assert v["source_reference"] == "GS Paper 1 Q42"
        assert v["source_year"] == 2024
        assert v["external_question_id"] == "UPSC-2024-Q42"

    def test_invalid_payload_rejected(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)
        # Blank text
        resp = api_client.post(
            "/api/v1/question-bank/questions/",
            {
                "text": "   ",
                "question_type": "MCQ",
                "difficulty": "EASY",
                "choices": [{"text": "A", "is_correct": True}],
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_incompatible_content_rejected(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)
        # MCQ question with descriptive content provided
        resp = api_client.post(
            "/api/v1/question-bank/questions/",
            {
                "text": "MCQ Question",
                "question_type": "MCQ",
                "difficulty": "EASY",
                "descriptive": {"marks": 10, "expected_answer": "Rubric"},
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_nonexistent_topic_rejected(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        fake_id = str(uuid.uuid4())
        resp = api_client.post(
            "/api/v1/question-bank/questions/",
            {
                "text": "MCQ Question",
                "question_type": "MCQ",
                "difficulty": "EASY",
                "topic_ids": [fake_id],
                "choices": [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "INVALID_TOPIC"


@pytest.mark.django_db
class TestQuestionRetrievalAPI:
    def test_retrieve_question_as_superadmin(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Retrieval",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "Opt 1", "is_correct": True}, {"text": "Opt 2", "is_correct": False}],
        )
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.get(f"/api/v1/question-bank/questions/{q.id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == str(q.id)
        assert "latest_version" in data
        assert data["latest_version"]["content"]["choices"][0]["is_correct"] is True

    def test_retrieve_nonexistent_question_returns_404(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        fake_id = uuid.uuid4()
        resp = api_client.get(f"/api/v1/question-bank/questions/{fake_id}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_student_cannot_retrieve_draft_question(self, api_client, student_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Draft Question",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        api_client.force_authenticate(user=student_user)
        # Draft question has no published version, so it is invisible to students (404)
        resp = api_client.get(f"/api/v1/question-bank/questions/{q.id}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_student_retrieves_sanitized_published_question(self, api_client, student_user, superadmin_user, topic):
        # Create and publish question as superadmin
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Published Question",
            difficulty=Difficulty.MEDIUM,
            topic_ids=[topic.id],
            choices=[{"text": "Opt 1", "is_correct": True}, {"text": "Opt 2", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/submit-review/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/approve/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/publish/")

        # Now retrieve as student
        api_client.force_authenticate(user=student_user)
        resp = api_client.get(f"/api/v1/question-bank/questions/{q.id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "published_version" in data
        assert "latest_version" not in data  # No internal editorial details
        # Choices should NOT have is_correct
        for choice in data["published_version"]["content"]["choices"]:
            assert "is_correct" not in choice

    def test_question_list_pagination(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)
        for i in range(25):
            create_question(
                question_type=QuestionType.MCQ,
                text=f"Question {i}",
                difficulty=Difficulty.EASY,
                topic_ids=[topic.id],
                choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
            )
        resp = api_client.get("/api/v1/question-bank/questions/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 25
        assert len(data["results"]) == 20
        assert data["next"] is not None

    def test_question_list_filtering_and_search(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)
        create_question(
            question_type=QuestionType.MCQ,
            text="Geography Himalayas question",
            difficulty=Difficulty.HARD,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        create_question(
            question_type=QuestionType.DESCRIPTIVE,
            text="Polity Parliament question",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            descriptive_data={"marks": 10, "expected_answer": "Answer"},
        )

        # Filter by question_type
        resp = api_client.get("/api/v1/question-bank/questions/?question_type=MCQ")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 1

        # Filter by difficulty
        resp = api_client.get("/api/v1/question-bank/questions/?difficulty=HARD")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 1

        # Search by text
        resp = api_client.get("/api/v1/question-bank/questions/?search=parliament")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 1


@pytest.mark.django_db
class TestQuestionVersionCreationAPI:
    def test_superadmin_can_create_new_version(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Version 1",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        api_client.force_authenticate(user=superadmin_user)
        payload = {
            "text": "Version 2 text",
            "question_type": "MCQ",
            "difficulty": "MEDIUM",
            "choices": [{"text": "A2", "is_correct": True}, {"text": "B2", "is_correct": False}],
        }
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["version_number"] == 2
        assert data["status"] == "DRAFT"
        assert data["text"] == "Version 2 text"


@pytest.mark.django_db
class TestQuestionVersionPatchAPI:
    def test_patch_draft_version_succeeds(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Initial text",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.patch(
            f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/",
            {"text": "Updated text via PATCH", "difficulty": "HARD"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["text"] == "Updated text via PATCH"
        assert data["difficulty"] == "HARD"

    def test_patch_cannot_modify_version_number_or_status(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Initial text",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)

        # Attempt to modify status via PATCH
        resp = api_client.patch(
            f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/",
            {"status": "PUBLISHED"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in resp.json()["error"]["fields"]

    def test_patch_immutable_version_rejected(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Approved Question",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/submit-review/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/approve/")

        # Attempt to patch approved version
        resp = api_client.patch(
            f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/",
            {"text": "Attempted edit"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "IMMUTABLE_VERSION"


@pytest.mark.django_db
class TestQuestionLifecycleAPI:
    def test_full_lifecycle_flow(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Lifecycle Question",
            difficulty=Difficulty.MEDIUM,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)

        # 1. Submit review
        r1 = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/submit-review/")
        assert r1.status_code == status.HTTP_200_OK
        assert r1.json()["status"] == "REVIEW"

        # 2. Approve
        r2 = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/approve/")
        assert r2.status_code == status.HTTP_200_OK
        assert r2.json()["status"] == "APPROVED"

        # 3. Publish
        r3 = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/publish/")
        assert r3.status_code == status.HTTP_200_OK
        assert r3.json()["status"] == "PUBLISHED"

        # 4. Archive
        r4 = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/archive/")
        assert r4.status_code == status.HTTP_200_OK
        assert r4.json()["status"] == "ARCHIVED"

    def test_illegal_lifecycle_transition_returns_400(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Draft Question",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)

        # Cannot directly publish DRAFT version
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/publish/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    def test_incomplete_question_cannot_be_published(self, api_client, superadmin_user, topic):
        # MCQ with 0 correct choices
        q = create_question(
            question_type=QuestionType.MCQ,
            text="Incomplete Question",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": False}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/submit-review/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/approve/")

        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/publish/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "PUBLICATION_VALIDATION_ERROR"

    def test_duplicate_published_version_returns_409_conflict(self, api_client, superadmin_user, topic):
        q = create_question(
            question_type=QuestionType.MCQ,
            text="V1",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v1 = q.latest_version
        api_client.force_authenticate(user=superadmin_user)
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v1.id}/submit-review/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v1.id}/approve/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v1.id}/publish/")

        # Create v2 and approve it
        r = api_client.post(
            f"/api/v1/question-bank/questions/{q.id}/versions/",
            {
                "text": "V2",
                "question_type": "MCQ",
                "difficulty": "EASY",
                "choices": [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
            },
            format="json",
        )
        v2_id = r.json()["id"]
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v2_id}/submit-review/")
        api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v2_id}/approve/")

        # Attempt to publish v2 while v1 is still published
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v2_id}/publish/")
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert resp.json()["error"]["code"] == "PUBLICATION_CONFLICT"


@pytest.mark.django_db
class TestArchitecturalAudit:
    """
    Targeted architectural audit tests verifying:
    1. PATCH goes through update_question_version application use case.
    2. Descriptive content rejects extraneous undeclared fields (no silent data loss).
    3. Assertion/Reason boolean derivation for all four domain relationships and rejection of invalid combinations.
    4. Match-following validation and cross-item error handling.
    5. Superuser without Superadmin group is rejected across all write and lifecycle endpoints.
    """

    def test_draft_patch_invokes_update_question_version_application_use_case(
        self, api_client, superadmin_user, topic
    ):
        q = create_question(
            question_type=QuestionType.DESCRIPTIVE,
            text="Initial Prompt",
            difficulty=Difficulty.MEDIUM,
            topic_ids=[topic.id],
            descriptive_data={"marks": 10, "expected_answer": "Initial Answer"},
        )
        v = q.latest_version
        api_client.force_authenticate(user=superadmin_user)

        resp = api_client.patch(
            f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/",
            {
                "text": "Updated Prompt",
                "difficulty": "HARD",
                "explanation": "Updated Explanation",
                "descriptive": {"marks": 20, "expected_answer": "Updated Answer"},
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        v.refresh_from_db()
        assert v.text == "Updated Prompt"
        assert v.difficulty == Difficulty.HARD
        assert v.explanation == "Updated Explanation"
        assert v.descriptive_content.marks == 20
        assert v.descriptive_content.expected_answer == "Updated Answer"

    def test_descriptive_extraneous_fields_rejected(self, api_client, superadmin_user, topic):
        """Undeclared descriptive fields (e.g. min_words, rubric) must be rejected, not silently ignored."""
        api_client.force_authenticate(user=superadmin_user)
        payload = {
            "text": "Write an essay.",
            "question_type": QuestionType.DESCRIPTIVE,
            "difficulty": Difficulty.MEDIUM,
            "topic_ids": [str(topic.id)],
            "descriptive": {
                "marks": 20,
                "expected_answer": "Good essay rubric.",
                "min_words": 150,
                "max_words": 300,
                "rubric": "Extra rubric data",
            },
        }
        resp = api_client.post("/api/v1/question-bank/questions/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        error_data = resp.json()["error"]
        assert error_data["code"] == "VALIDATION_ERROR"
        assert "descriptive" in error_data["fields"]

    @pytest.mark.parametrize(
        "a_true,r_true,explains,expected_relationship",
        [
            (True, True, True, AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT),
            (True, True, False, AssertionReasonRelationship.BOTH_TRUE_REASON_NOT_CORRECT),
            (True, False, False, AssertionReasonRelationship.ASSERTION_TRUE_REASON_FALSE),
            (False, False, False, AssertionReasonRelationship.ASSERTION_FALSE_REASON_FALSE),
        ],
    )
    def test_assertion_reason_all_four_relationships_via_boolean_derivation(
        self, api_client, superadmin_user, topic, a_true, r_true, explains, expected_relationship
    ):
        api_client.force_authenticate(user=superadmin_user)
        payload = {
            "text": "AR question stem",
            "question_type": QuestionType.ASSERTION_REASON,
            "difficulty": Difficulty.MEDIUM,
            "topic_ids": [str(topic.id)],
            "assertion_reason": {
                "assertion_text": "The sky is blue.",
                "reason_text": "Rayleigh scattering occurs in the atmosphere.",
                "assertion_true": a_true,
                "reason_true": r_true,
                "reason_explains_assertion": explains,
            },
        }
        resp = api_client.post("/api/v1/question-bank/questions/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        q_id = resp.json()["id"]
        q = Question.objects.get(id=q_id)
        ar = q.latest_version.assertion_reason_content
        assert ar.correct_relationship == expected_relationship

    def test_assertion_reason_invalid_combinations_rejected(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)

        # 1. assertion_true=False, reason_true=True (not an accepted domain relationship)
        payload1 = {
            "text": "AR stem",
            "question_type": QuestionType.ASSERTION_REASON,
            "difficulty": Difficulty.MEDIUM,
            "topic_ids": [str(topic.id)],
            "assertion_reason": {
                "assertion": "False assertion",
                "reason": "True reason",
                "assertion_true": False,
                "reason_true": True,
            },
        }
        resp1 = api_client.post("/api/v1/question-bank/questions/", payload1, format="json")
        assert resp1.status_code == status.HTTP_400_BAD_REQUEST

        # 2. explains=True when assertion is false
        payload2 = {
            "text": "AR stem",
            "question_type": QuestionType.ASSERTION_REASON,
            "difficulty": Difficulty.MEDIUM,
            "topic_ids": [str(topic.id)],
            "assertion_reason": {
                "assertion": "False assertion",
                "reason": "False reason",
                "assertion_true": False,
                "reason_true": False,
                "reason_explains_assertion": True,
            },
        }
        resp2 = api_client.post("/api/v1/question-bank/questions/", payload2, format="json")
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST

        # 3. Contradictory explicit relationship vs boolean flags
        payload3 = {
            "text": "AR stem",
            "question_type": QuestionType.ASSERTION_REASON,
            "difficulty": Difficulty.MEDIUM,
            "topic_ids": [str(topic.id)],
            "assertion_reason": {
                "assertion": "Assertion",
                "reason": "Reason",
                "assertion_true": True,
                "reason_true": False,
                "correct_relationship": AssertionReasonRelationship.BOTH_TRUE_REASON_CORRECT,
            },
        }
        resp3 = api_client.post("/api/v1/question-bank/questions/", payload3, format="json")
        assert resp3.status_code == status.HTTP_400_BAD_REQUEST

    def test_match_following_invalid_pair_reference_rejected(self, api_client, superadmin_user, topic):
        api_client.force_authenticate(user=superadmin_user)
        payload = {
            "text": "Match capitals",
            "question_type": QuestionType.MATCH_FOLLOWING,
            "difficulty": Difficulty.EASY,
            "topic_ids": [str(topic.id)],
            "match_following": {
                "left_items": [{"text": "France", "position": 1}, {"text": "Germany", "position": 2}],
                "right_items": [{"text": "Paris", "position": 1}, {"text": "Berlin", "position": 2}],
                "pairs": [
                    {"left_position": 1, "right_position": 1},
                    {"left_position": 99, "right_position": 2},  # Non-existent left_position 99
                ],
            },
        }
        resp = api_client.post("/api/v1/question-bank/questions/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_superuser_without_superadmin_group_rejected_for_patch_and_lifecycle(
        self, api_client, superuser_only_user, topic
    ):
        """is_superuser without Superadmin group must NOT be permitted to PATCH or mutate lifecycle."""
        q = create_question(
            question_type=QuestionType.MCQ,
            text="MCQ Prompt",
            difficulty=Difficulty.EASY,
            topic_ids=[topic.id],
            choices=[{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
        )
        v = q.latest_version
        api_client.force_authenticate(user=superuser_only_user)

        # PATCH
        resp = api_client.patch(
            f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/",
            {"text": "Attempted Hack"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # submit-review
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/submit-review/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # approve
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/approve/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # publish
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/publish/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # archive
        resp = api_client.post(f"/api/v1/question-bank/questions/{q.id}/versions/{v.id}/archive/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

