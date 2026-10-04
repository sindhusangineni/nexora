from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.identity.permissions.roles import ROLE_SUPERADMIN
from apps.question_bank.application import (
    approve_question_version,
    archive_question_version,
    create_question_version,
    publish_question_version,
    submit_question_version_for_review,
    update_question_version,
)
from apps.question_bank.filters import (
    QuestionBankFilterBackend,
    QuestionVersionFilter,
)
from apps.question_bank.models import (
    Question,
    QuestionStatus,
    QuestionVersion,
)
from apps.question_bank.pagination import QuestionBankPagination
from apps.question_bank.permissions import (
    IsSuperadminOnly,
    IsSuperadminOrStudentReadOnly,
)
from apps.question_bank.serializers import (
    QuestionVersionAdminResponseSerializer,
    QuestionVersionCreateSerializer,
    QuestionVersionPatchSerializer,
    QuestionVersionStudentResponseSerializer,
)
from apps.question_bank.validators import validate_single_content_representation
from shared.api.errors import ErrorResponseSerializer


@extend_schema(
    tags=["Question Bank"],
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        status.HTTP_409_CONFLICT: ErrorResponseSerializer,
    },
)
class QuestionVersionViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing QuestionVersion resources and lifecycle state actions:
    - Lists and retrieves versions belonging to a Question.
    - Creates new editorial versions via application use cases.
    - Allows PATCH modifications exclusively on DRAFT versions.
    - Exposes explicit lifecycle endpoints: submit-review, approve, publish, archive.
    """

    lookup_field = "id"
    lookup_url_kwarg = "version_id"
    queryset = QuestionVersion.objects.none()
    pagination_class = QuestionBankPagination
    filter_backends = (QuestionBankFilterBackend,)
    filterset_class = QuestionVersionFilter

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsSuperadminOrStudentReadOnly()]
        return [IsSuperadminOnly()]

    def _ensure_question_exists(self):
        if getattr(self, "swagger_fake_view", False):
            return
        question_id = self.kwargs.get("question_id")
        if not question_id:
            return
        user = self.request.user
        qs = Question.objects.all()
        if not (user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists()):
            qs = qs.filter(versions__status=QuestionStatus.PUBLISHED)

        if not qs.filter(id=question_id).exists():
            raise exceptions.NotFound(f"Question '{question_id}' not found.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return QuestionVersion.objects.none()
        self._ensure_question_exists()
        question_id = self.kwargs.get("question_id")
        user = self.request.user

        base_qs = QuestionVersion.objects.filter(question_id=question_id).prefetch_related(
            "choices", "match_items", "match_pairs"
        )
        if user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists():
            return base_qs

        return base_qs.filter(status=QuestionStatus.PUBLISHED)

    def get_serializer_class(self):
        if self.action == "create":
            return QuestionVersionCreateSerializer
        if self.action == "partial_update":
            return QuestionVersionPatchSerializer

        user = self.request.user
        if user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists():
            return QuestionVersionAdminResponseSerializer

        return QuestionVersionStudentResponseSerializer

    @extend_schema(
        summary="List Question Versions",
        description="Returns a paginated list of versions for a specific Question.",
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Retrieve Question Version",
        description="Retrieves a specific editorial version of a Question.",
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Create Question Version",
        description="Creates a new editorial version for this Question (begins in DRAFT).",
        request=QuestionVersionCreateSerializer,
        responses={status.HTTP_201_CREATED: QuestionVersionAdminResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        self._ensure_question_exists()
        question_id = self.kwargs.get("question_id")

        serializer = QuestionVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        version = create_question_version(
            question_id,
            question_type=data["question_type"],
            text=data["text"],
            difficulty=data["difficulty"],
            explanation=data.get("explanation", ""),
            topic_ids=data.get("topic_ids"),
            source_type=data.get("source_type"),
            source_name=data.get("source_name"),
            source_reference=data.get("source_reference"),
            source_year=data.get("source_year"),
            external_question_id=data.get("external_question_id"),
            choices=data.get("choices"),
            true_false_data=data.get("true_false"),
            assertion_reason_data=data.get("assertion_reason"),
            match_following_data=data.get("match_following"),
            descriptive_data=data.get("descriptive"),
        )

        response_serializer = QuestionVersionAdminResponseSerializer(version)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update DRAFT Version",
        description="Partially updates editable fields of a DRAFT version. Immutable versions reject modification.",
        request=QuestionVersionPatchSerializer,
        responses={status.HTTP_200_OK: QuestionVersionAdminResponseSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        version = self.get_object()

        serializer = QuestionVersionPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        update_kwargs = {}
        for field in (
            "text",
            "difficulty",
            "explanation",
            "topic_ids",
            "source_type",
            "source_name",
            "source_reference",
            "source_year",
            "external_question_id",
        ):
            if field in data:
                update_kwargs[field] = data[field]

        if "choices" in data:
            update_kwargs["choices"] = data["choices"]
        if "true_false" in data:
            update_kwargs["true_false_data"] = data["true_false"]
        if "assertion_reason" in data:
            update_kwargs["assertion_reason_data"] = data["assertion_reason"]
        if "match_following" in data:
            update_kwargs["match_following_data"] = data["match_following"]
        if "descriptive" in data:
            update_kwargs["descriptive_data"] = data["descriptive"]

        updated_version = update_question_version(version.id, **update_kwargs)
        response_serializer = QuestionVersionAdminResponseSerializer(updated_version)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Submit Version for Review",
        description="Transitions a DRAFT version to REVIEW status.",
        request=None,
        responses={status.HTTP_200_OK: QuestionVersionAdminResponseSerializer},
    )
    @action(detail=True, methods=["post"], url_path="submit-review")
    def submit_review(self, request, *args, **kwargs):
        version = self.get_object()
        updated = submit_question_version_for_review(version.id)
        serializer = QuestionVersionAdminResponseSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Approve Version",
        description="Transitions a version under REVIEW to APPROVED status.",
        request=None,
        responses={status.HTTP_200_OK: QuestionVersionAdminResponseSerializer},
    )
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, *args, **kwargs):
        version = self.get_object()
        updated = approve_question_version(version.id)
        serializer = QuestionVersionAdminResponseSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Publish Version",
        description="Publishes an APPROVED version after running publication completeness validation.",
        request=None,
        responses={status.HTTP_200_OK: QuestionVersionAdminResponseSerializer},
    )
    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, *args, **kwargs):
        version = self.get_object()
        updated = publish_question_version(version.id)
        serializer = QuestionVersionAdminResponseSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Archive Version",
        description="Transitions a PUBLISHED version to the terminal ARCHIVED state.",
        request=None,
        responses={status.HTTP_200_OK: QuestionVersionAdminResponseSerializer},
    )
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, *args, **kwargs):
        version = self.get_object()
        updated = archive_question_version(version.id)
        serializer = QuestionVersionAdminResponseSerializer(updated)
        return Response(serializer.data, status=status.HTTP_200_OK)
