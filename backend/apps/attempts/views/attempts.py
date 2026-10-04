from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attempts.application import (
    clear_response,
    save_response,
    start_attempt,
    submit_attempt,
)
from apps.attempts.authorization import get_authorization_context
from apps.attempts.exceptions import (
    AttemptAuthorizationError,
    AttemptNotFoundError,
    InvalidAttemptStateError,
)
from apps.attempts.models import Attempt, AttemptResult
from apps.attempts.models.enums import AttemptStatus
from apps.attempts.pagination import AttemptPagination
from apps.attempts.permissions import IsStudentOnly, IsStudentOrSuperadmin
from apps.attempts.serializers import (
    AttemptDeliverySerializer,
    AttemptHistorySummarySerializer,
    AttemptResponseDeliverySerializer,
    AttemptResultSerializer,
    SaveResponseRequestSerializer,
    StartAttemptRequestSerializer,
)
from shared.api.errors import ErrorResponseSerializer


class AttemptListCreateView(APIView):
    """
    List student attempt history or start a new attempt for an assessment paper.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStudentOnly()]
        return [IsStudentOrSuperadmin()]

    @extend_schema(
        summary="List student attempt history",
        description="Returns paginated attempt history for the authenticated student, ordered newest first.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filter by attempt lifecycle status (IN_PROGRESS, SUBMITTED, EVALUATED, CANCELLED)",
                required=False,
                type=str,
                enum=AttemptStatus.values,
            ),
            OpenApiParameter(
                name="page",
                description="A page number within the paginated result set.",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="page_size",
                description="Number of results to return per page (max 100).",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: AttemptHistorySummarySerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden"),
        },
        tags=["Attempts"],
    )
    def get(self, request):
        queryset = (
            Attempt.objects.filter(student_id=request.user.id)
            .select_related("result")
            .order_by("-started_at", "-created_at")
        )

        status_param = request.query_params.get("status")
        if status_param and status_param in AttemptStatus.values:
            queryset = queryset.filter(status=status_param)

        paginator = AttemptPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = AttemptHistorySummarySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AttemptHistorySummarySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Start or resume an assessment attempt",
        description="Creates a new attempt for the given paper or idempotently returns the student's active attempt.",
        request=StartAttemptRequestSerializer,
        responses={
            201: AttemptDeliverySerializer,
            200: AttemptDeliverySerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Validation or eligibility error"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Student role required"),
        },
        tags=["Attempts"],
    )
    def post(self, request):
        serializer = StartAttemptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        paper_id = serializer.validated_data["assessment_paper_id"]
        auth_context = get_authorization_context(request.user)

        attempt = start_attempt(
            student_id=request.user.id,
            paper_id=paper_id,
            authorization_context=auth_context,
        )

        # Prefetch relations for delivery serialization
        attempt = (
            Attempt.objects.filter(id=attempt.id)
            .prefetch_related(
                "items__choices",
                "items__response__choices",
                "items__response__matches",
            )
            .first()
        )
        return Response(AttemptDeliverySerializer(attempt).data, status=status.HTTP_201_CREATED)


class AttemptDetailView(APIView):
    """
    Retrieve delivery-safe attempt data.
    Never exposes answer keys, explanations, or grading internals.
    """

    permission_classes = [IsStudentOrSuperadmin]

    @extend_schema(
        summary="Get active attempt delivery",
        description="Retrieves delivery-safe snapshot and items for an attempt. Only the student owner or Superadmin can access.",
        responses={
            200: AttemptDeliverySerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden access to another student's attempt"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not found"),
        },
        tags=["Attempts"],
    )
    def get(self, request, attempt_id):
        attempt = (
            Attempt.objects.filter(id=attempt_id)
            .prefetch_related(
                "items__choices",
                "items__response__choices",
                "items__response__matches",
            )
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        auth_context = get_authorization_context(request.user)
        if not auth_context.is_superadmin and attempt.student_id != auth_context.actor_id:
            raise AttemptAuthorizationError("Students may only view their own test attempts.")

        return Response(AttemptDeliverySerializer(attempt).data, status=status.HTTP_200_OK)


class AttemptItemResponseView(APIView):
    """
    Save or clear student responses on an attempt item.
    Student-only access.
    """

    permission_classes = [IsStudentOnly]

    @extend_schema(
        summary="Save student response on an item",
        description="Records or updates a student answer on an active AttemptItem. Rejects if attempt has expired.",
        request=SaveResponseRequestSerializer,
        responses={
            200: AttemptResponseDeliverySerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Invalid response structure"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt or item not found"),
            409: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt expired or conflict"),
        },
        tags=["Attempts"],
    )
    def put(self, request, attempt_id, item_id):
        return self._save(request, attempt_id, item_id)

    @extend_schema(
        summary="Patch student response on an item",
        description="Records or updates a student answer on an active AttemptItem. Rejects if attempt has expired.",
        request=SaveResponseRequestSerializer,
        responses={
            200: AttemptResponseDeliverySerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Invalid response structure"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt or item not found"),
            409: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt expired or conflict"),
        },
        tags=["Attempts"],
    )
    def patch(self, request, attempt_id, item_id):
        return self._save(request, attempt_id, item_id)

    def _save(self, request, attempt_id, item_id):
        serializer = SaveResponseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = Attempt.objects.filter(id=attempt_id).first()
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        from apps.attempts.services.scoring import get_scoring_policy
        scoring_policy = get_scoring_policy(attempt.score_floor_policy)

        auth_context = get_authorization_context(request.user)
        updated_resp = save_response(
            attempt_id=attempt_id,
            attempt_item_id=item_id,
            authorization=auth_context,
            response_data=serializer.validated_data,
            scoring_policy=scoring_policy,
        )
        return Response(AttemptResponseDeliverySerializer(updated_resp).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Clear student response on an item",
        description="Resets a previously answered item back to UNANSWERED.",
        responses={
            200: AttemptResponseDeliverySerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt or item not found"),
            409: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt expired or conflict"),
        },
        tags=["Attempts"],
    )
    def delete(self, request, attempt_id, item_id):
        attempt = Attempt.objects.filter(id=attempt_id).first()
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        from apps.attempts.services.scoring import get_scoring_policy
        scoring_policy = get_scoring_policy(attempt.score_floor_policy)

        auth_context = get_authorization_context(request.user)
        cleared_resp = clear_response(
            attempt_id=attempt_id,
            attempt_item_id=item_id,
            authorization=auth_context,
            scoring_policy=scoring_policy,
        )
        return Response(AttemptResponseDeliverySerializer(cleared_resp).data, status=status.HTTP_200_OK)


class AttemptSubmitView(APIView):
    """
    Submit an attempt.
    Student-only access.
    """

    permission_classes = [IsStudentOnly]

    @extend_schema(
        summary="Submit an assessment attempt",
        description="Finalizes and evaluates student attempt. Transitions to EVALUATED (objective) or SUBMITTED (descriptive).",
        request=None,
        responses={
            200: AttemptDeliverySerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not in progress"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not found"),
        },
        tags=["Attempts"],
    )
    def post(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id).first()
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        from apps.attempts.services.scoring import get_scoring_policy
        scoring_policy = get_scoring_policy(attempt.score_floor_policy)

        auth_context = get_authorization_context(request.user)
        attempt, result = submit_attempt(
            attempt_id=attempt_id,
            authorization=auth_context,
            scoring_policy=scoring_policy,
        )

        attempt = (
            Attempt.objects.filter(id=attempt.id)
            .prefetch_related(
                "items__choices",
                "items__response__choices",
                "items__response__matches",
            )
            .first()
        )
        return Response(AttemptDeliverySerializer(attempt).data, status=status.HTTP_200_OK)


class AttemptResultView(APIView):
    """
    Retrieve scorecard for an attempt.
    """

    permission_classes = [IsStudentOrSuperadmin]

    @extend_schema(
        summary="Get attempt result",
        description="Retrieves the result scorecard for an attempt. Reflects PENDING or FINAL status.",
        responses={
            200: AttemptResultSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not submitted or result not ready"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Forbidden"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt or result not found"),
        },
        tags=["Attempts"],
    )
    def get(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id).first()
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        auth_context = get_authorization_context(request.user)
        if not auth_context.is_superadmin and attempt.student_id != auth_context.actor_id:
            raise AttemptAuthorizationError("Students may only view their own test results.")

        if attempt.status == AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStateError("Cannot retrieve result for an attempt that is still in progress.")

        result = (
            AttemptResult.objects.filter(attempt=attempt)
            .select_related("attempt")
            .prefetch_related("section_results")
            .first()
        )
        if result is None:
            raise InvalidAttemptStateError("Result for this attempt is not available.")

        return Response(AttemptResultSerializer(result).data, status=status.HTTP_200_OK)

