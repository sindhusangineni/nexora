from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.identity.permissions.roles import ROLE_SUPERADMIN
from apps.question_bank.application import create_question
from apps.question_bank.filters import QuestionBankFilterBackend, QuestionFilter
from apps.question_bank.models import Question, QuestionStatus
from apps.question_bank.pagination import QuestionBankPagination
from apps.question_bank.permissions import IsSuperadminOrStudentReadOnly
from apps.question_bank.serializers import (
    QuestionAdminResponseSerializer,
    QuestionCreateSerializer,
    QuestionStudentResponseSerializer,
)
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
class QuestionViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing Question aggregates:
    - Lists and retrieves questions with role-based representations.
    - Superadmin: authoring view (all statuses, answers, provenance).
    - Student: sanitized view of published questions only.
    - Creates new questions atomically via the application use case.
    """

    lookup_field = "id"
    lookup_url_kwarg = "question_id"
    queryset = Question.objects.none()
    permission_classes = [IsSuperadminOrStudentReadOnly]
    pagination_class = QuestionBankPagination
    filter_backends = (QuestionBankFilterBackend,)
    filterset_class = QuestionFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Question.objects.none()
        user = self.request.user
        base_qs = Question.objects.all().prefetch_related(
            "question_topics",
            "versions",
            "versions__choices",
        )

        if user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists():
            return base_qs

        # Students only see questions that have at least one PUBLISHED version
        return base_qs.filter(versions__status=QuestionStatus.PUBLISHED).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return QuestionCreateSerializer

        user = self.request.user
        if user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists():
            return QuestionAdminResponseSerializer

        return QuestionStudentResponseSerializer

    @extend_schema(
        summary="List Questions",
        description="Returns a paginated list of Questions with role-based representation.",
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
        summary="Retrieve Question",
        description="Retrieves a single Question aggregate by ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Create Question",
        description="Creates a new Question aggregate and its initial DRAFT version via the application use case.",
        request=QuestionCreateSerializer,
        responses={status.HTTP_201_CREATED: QuestionAdminResponseSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        question = create_question(
            question_type=data["question_type"],
            text=data["text"],
            difficulty=data["difficulty"],
            explanation=data.get("explanation", ""),
            topic_ids=data.get("topic_ids", []),
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

        response_serializer = QuestionAdminResponseSerializer(question)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
