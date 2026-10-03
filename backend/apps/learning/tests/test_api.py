import uuid
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

from apps.learning.models import Chapter, Domain, Subject, Topic

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
def unassigned_user():
    return User.objects.create_user(email="unassigned@example.com", password="StrongPassword123!")


@pytest.fixture
def superuser_only_user():
    return User.objects.create_superuser(
        email="superuser_only@example.com",
        password="StrongPassword123!",
    )


@pytest.mark.django_db
class TestLearningAPIAuthenticationAndRBAC:
    def test_anonymous_requests_rejected_with_401(self, api_client):
        # List
        resp = api_client.get("/api/v1/learning/domains/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

        # Create
        resp = api_client.post("/api/v1/learning/domains/", {"name": "Test"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    def test_student_read_allowed(self, api_client, student_user):
        Domain.objects.create(name="Civil Services")
        api_client.force_authenticate(user=student_user)

        resp = api_client.get("/api/v1/learning/domains/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["name"] == "Civil Services"

    def test_student_mutation_rejected_with_403(self, api_client, student_user):
        domain = Domain.objects.create(name="Civil Services")
        api_client.force_authenticate(user=student_user)

        # POST
        resp = api_client.post("/api/v1/learning/domains/", {"name": "Engineering"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # PATCH
        resp = api_client.patch(f"/api/v1/learning/domains/{domain.id}/", {"name": "Updated"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # DELETE
        resp = api_client.delete(f"/api/v1/learning/domains/{domain.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_authenticated_user_without_application_group_rejected_with_403(self, api_client, unassigned_user):
        """
        Authenticated user who belongs neither to the Student group nor the Superadmin group
        must be denied access to both read and mutation operations.
        """
        Domain.objects.create(name="Civil Services")
        api_client.force_authenticate(user=unassigned_user)

        # GET rejected
        resp = api_client.get("/api/v1/learning/domains/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # POST rejected
        resp = api_client.post("/api/v1/learning/domains/", {"name": "Engineering"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_superuser_without_superadmin_group_rejected_with_403(self, api_client, superuser_only_user):
        """
        Verify that is_superuser=True alone does not bypass Nexora RBAC.
        The user must belong to the Superadmin group to perform mutations or read curriculum resources.
        """
        domain = Domain.objects.create(name="Civil Services")
        api_client.force_authenticate(user=superuser_only_user)

        # GET rejected (neither Student nor Superadmin group)
        resp = api_client.get("/api/v1/learning/domains/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # POST rejected
        resp = api_client.post("/api/v1/learning/domains/", {"name": "Engineering"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # PATCH rejected
        resp = api_client.patch(f"/api/v1/learning/domains/{domain.id}/", {"name": "Updated"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

        # DELETE rejected
        resp = api_client.delete(f"/api/v1/learning/domains/{domain.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["error"]["code"] == "PERMISSION_DENIED"

    def test_superadmin_mutation_allowed(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)

        # POST
        resp = api_client.post("/api/v1/learning/domains/", {"name": "Civil Services"})
        assert resp.status_code == status.HTTP_201_CREATED
        domain_id = resp.json()["id"]

        # PATCH
        resp = api_client.patch(f"/api/v1/learning/domains/{domain_id}/", {"description": "Updated desc"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["description"] == "Updated desc"

        # DELETE
        resp = api_client.delete(f"/api/v1/learning/domains/{domain_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestLearningAPIHttpContract:
    def test_put_method_not_allowed(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        api_client.force_authenticate(user=superadmin_user)

        resp = api_client.put(f"/api/v1/learning/domains/{domain.id}/", {"name": "New Name"})
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestLearningAPICRUD:
    def test_domain_crud_lifecycle(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)

        # Create
        resp = api_client.post(
            "/api/v1/learning/domains/",
            {"name": "  Civil   Services  ", "description": "Prep"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        domain_id = data["id"]
        assert data["name"] == "Civil Services"
        assert data["description"] == "Prep"
        assert "created_at" in data
        assert "updated_at" in data

        # Detail
        resp = api_client.get(f"/api/v1/learning/domains/{domain_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == domain_id

        # Patch
        resp = api_client.patch(
            f"/api/v1/learning/domains/{domain_id}/",
            {"description": "Updated prep"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["description"] == "Updated prep"

        # Delete
        resp = api_client.delete(f"/api/v1/learning/domains/{domain_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Domain.objects.filter(id=domain_id).exists()

    def test_subject_crud_lifecycle(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        api_client.force_authenticate(user=superadmin_user)

        # Create
        resp = api_client.post(
            "/api/v1/learning/subjects/",
            {"domain": str(domain.id), "name": "Polity", "position": 1},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        subject_id = resp.json()["id"]
        assert resp.json()["domain"] == str(domain.id)
        assert resp.json()["name"] == "Polity"
        assert resp.json()["position"] == 1

        # Patch position & name
        resp = api_client.patch(
            f"/api/v1/learning/subjects/{subject_id}/",
            {"position": 5, "name": "Indian Polity"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["position"] == 5
        assert resp.json()["name"] == "Indian Polity"

        # Delete
        resp = api_client.delete(f"/api/v1/learning/subjects/{subject_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Subject.objects.filter(id=subject_id).exists()

    def test_chapter_crud_lifecycle(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity")
        api_client.force_authenticate(user=superadmin_user)

        # Create
        resp = api_client.post(
            "/api/v1/learning/chapters/",
            {"subject": str(subject.id), "name": "Preamble"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        chapter_id = resp.json()["id"]

        # Detail
        resp = api_client.get(f"/api/v1/learning/chapters/{chapter_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["name"] == "Preamble"

        # Delete
        resp = api_client.delete(f"/api/v1/learning/chapters/{chapter_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Chapter.objects.filter(id=chapter_id).exists()

    def test_topic_crud_lifecycle(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="Preamble")
        api_client.force_authenticate(user=superadmin_user)

        # Create
        resp = api_client.post(
            "/api/v1/learning/topics/",
            {"chapter": str(chapter.id), "name": "Secularism"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        topic_id = resp.json()["id"]

        # Patch
        resp = api_client.patch(
            f"/api/v1/learning/topics/{topic_id}/",
            {"description": "Article references"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["description"] == "Article references"

        # Delete
        resp = api_client.delete(f"/api/v1/learning/topics/{topic_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Topic.objects.filter(id=topic_id).exists()


@pytest.mark.django_db
class TestLearningAPIHierarchyAndRelationships:
    def test_nonexistent_parent_on_create_returns_400(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        non_existent_uuid = str(uuid.uuid4())

        resp = api_client.post(
            "/api/v1/learning/subjects/",
            {"domain": non_existent_uuid, "name": "History"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "domain" in data["error"]["fields"]

    def test_parent_reassignment_success(self, api_client, superadmin_user):
        d1 = Domain.objects.create(name="Domain 1")
        d2 = Domain.objects.create(name="Domain 2")
        subject = Subject.objects.create(domain=d1, name="History")

        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.patch(
            f"/api/v1/learning/subjects/{subject.id}/",
            {"domain": str(d2.id)},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["domain"] == str(d2.id)

        subject.refresh_from_db()
        assert subject.domain == d2

    def test_parent_reassignment_to_nonexistent_parent_returns_400(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Domain 1")
        subject = Subject.objects.create(domain=domain, name="History")

        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.patch(
            f"/api/v1/learning/subjects/{subject.id}/",
            {"domain": str(uuid.uuid4())},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.django_db
class TestLearningAPINameValidationAndUniqueness:
    def test_duplicate_domain_name_case_insensitive_rejected(self, api_client, superadmin_user):
        Domain.objects.create(name="History")
        api_client.force_authenticate(user=superadmin_user)

        resp = api_client.post("/api/v1/learning/domains/", {"name": "history"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "name" in data["error"]["fields"]

    def test_whitespace_normalized_duplicate_rejected(self, api_client, superadmin_user):
        Domain.objects.create(name="Indian Polity")
        api_client.force_authenticate(user=superadmin_user)

        resp = api_client.post("/api/v1/learning/domains/", {"name": "   indian    polity   "})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "name" in data["error"]["fields"]

    def test_blank_or_whitespace_only_name_rejected(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)

        resp = api_client.post("/api/v1/learning/domains/", {"name": "   "})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "name" in data["error"]["fields"]

    def test_same_subject_name_under_different_domains_allowed(self, api_client, superadmin_user):
        d1 = Domain.objects.create(name="Civil Services")
        d2 = Domain.objects.create(name="Engineering")
        Subject.objects.create(domain=d1, name="History")

        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.post(
            "/api/v1/learning/subjects/",
            {"domain": str(d2.id), "name": "History"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "History"


@pytest.mark.django_db
class TestLearningAPIFiltering:
    def test_search_name_only_match(self, api_client, student_user):
        Domain.objects.create(name="Constitution", description="Foundational laws")
        Domain.objects.create(name="Mechanics", description="Physics principles")
        api_client.force_authenticate(user=student_user)

        resp = api_client.get("/api/v1/learning/domains/?search=Constitution")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["name"] == "Constitution"

    def test_search_description_only_match(self, api_client, student_user):
        Domain.objects.create(name="Law", description="Detailed study of constitutional jurisprudence")
        Domain.objects.create(name="Physics", description="Study of matter and motion")
        api_client.force_authenticate(user=student_user)

        resp = api_client.get("/api/v1/learning/domains/?search=jurisprudence")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["name"] == "Law"

    def test_search_case_insensitive_match(self, api_client, student_user):
        Domain.objects.create(name="Indian Polity", description="Covers fundamental rights and duties")
        api_client.force_authenticate(user=student_user)

        # Uppercase search matching lowercase/mixed in name
        resp = api_client.get("/api/v1/learning/domains/?search=POLITY")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 1

        # Mixed-case search matching lowercase in description
        resp = api_client.get("/api/v1/learning/domains/?search=fUnDaMeNtAl")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 1

    def test_parent_filter_and_search_work_together(self, api_client, student_user):
        d1 = Domain.objects.create(name="Civil Services")
        d2 = Domain.objects.create(name="Engineering")
        s1 = Subject.objects.create(domain=d1, name="Polity", description="Indian governance")
        s2 = Subject.objects.create(domain=d1, name="History", description="Ancient and modern")
        s3 = Subject.objects.create(domain=d2, name="Polity", description="Campus governance")

        api_client.force_authenticate(user=student_user)

        # Searching for 'governance' within Domain 1 returns only Subject 1
        resp = api_client.get(f"/api/v1/learning/subjects/?domain={d1.id}&search=governance")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["id"] == str(s1.id)

    def test_search_non_matching_returns_empty_results(self, api_client, student_user):
        Domain.objects.create(name="Civil Services", description="Civil exam preparation")
        api_client.force_authenticate(user=student_user)

        resp = api_client.get("/api/v1/learning/domains/?search=nonexistenttermxyz")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_invalid_uuid_filter_returns_400(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        resp = api_client.get("/api/v1/learning/subjects/?domain=not-a-valid-uuid")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "domain" in data["error"]["fields"]

    def test_valid_nonexistent_uuid_returns_empty_result(self, api_client, student_user):
        api_client.force_authenticate(user=student_user)
        random_uuid = str(uuid.uuid4())
        resp = api_client.get(f"/api/v1/learning/subjects/?domain={random_uuid}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []


@pytest.mark.django_db
class TestLearningAPIPagination:
    def test_default_pagination_structure(self, api_client, student_user):
        for i in range(25):
            Domain.objects.create(name=f"Domain {i:02d}")

        api_client.force_authenticate(user=student_user)
        resp = api_client.get("/api/v1/learning/domains/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        assert data["count"] == 25
        assert data["next"] is not None
        assert data["previous"] is None
        assert len(data["results"]) == 20  # default page size 20

    def test_custom_page_size_and_max_page_size(self, api_client, student_user):
        for i in range(25):
            Domain.objects.create(name=f"Domain {i:02d}")

        api_client.force_authenticate(user=student_user)

        # Custom page size 10
        resp = api_client.get("/api/v1/learning/domains/?page_size=10")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) == 10

        # Page 2
        resp = api_client.get("/api/v1/learning/domains/?page=2&page_size=10")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) == 10


@pytest.mark.django_db
class TestLearningAPIDeletionProtection:
    def test_protected_domain_deletion_returns_409(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        Subject.objects.create(domain=domain, name="Polity")

        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.delete(f"/api/v1/learning/domains/{domain.id}/")
        assert resp.status_code == status.HTTP_409_CONFLICT
        data = resp.json()
        assert data["error"]["code"] == "PROTECTED_RESOURCE"
        assert "Cannot delete" in data["error"]["message"]

        # Verify domain still exists
        assert Domain.objects.filter(id=domain.id).exists()

    def test_protected_subject_deletion_returns_409(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity")
        Chapter.objects.create(subject=subject, name="Preamble")

        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.delete(f"/api/v1/learning/subjects/{subject.id}/")
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert resp.json()["error"]["code"] == "PROTECTED_RESOURCE"
        assert Subject.objects.filter(id=subject.id).exists()

    def test_protected_chapter_deletion_returns_409(self, api_client, superadmin_user):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="Preamble")
        Topic.objects.create(chapter=chapter, name="Socialist")

        api_client.force_authenticate(user=superadmin_user)
        resp = api_client.delete(f"/api/v1/learning/chapters/{chapter.id}/")
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert resp.json()["error"]["code"] == "PROTECTED_RESOURCE"
        assert Chapter.objects.filter(id=chapter.id).exists()
