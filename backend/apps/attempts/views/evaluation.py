from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attempts.application import cancel_attempt, evaluate_descriptive_item
from apps.attempts.authorization import get_authorization_context
from apps.attempts.exceptions import AttemptNotFoundError
from apps.attempts.models import Attempt
from apps.attempts.permissions import IsSuperadminOnly
from apps.attempts.serializers import (
    AttemptEvaluationReviewSerializer,
    AttemptReviewSerializer,
    CancelAttemptRequestSerializer,
    EvaluateDescriptiveRequestSerializer,
)
from shared.api.errors import ErrorResponseSerializer


class AttemptItemEvaluateView(APIView):
    """
    Manually evaluate a descriptive item.
    Superadmin-only access.
    """

    permission_classes = [IsSuperadminOnly]

    @extend_schema(
        summary="Evaluate a descriptive question item",
        description="Records marks and evaluation comments for a descriptive item and recalculates overall attempt score.",
        request=EvaluateDescriptiveRequestSerializer,
        responses={
            200: AttemptEvaluationReviewSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Invalid evaluation parameters or item not pending"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Superadmin role required"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt or item not found"),
        },
        tags=["Attempts"],
    )
    def post(self, request, attempt_id, item_id):
        serializer = EvaluateDescriptiveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_context = get_authorization_context(request.user)
        _, _, evaluation, _ = evaluate_descriptive_item(
            attempt_id=attempt_id,
            attempt_item_id=item_id,
            evaluation_state=serializer.validated_data["evaluation_state"],
            marks_awarded=serializer.validated_data.get("marks_awarded"),
            marks_deducted=serializer.validated_data.get("marks_deducted"),
            evaluation_comments=serializer.validated_data.get("evaluation_comments"),
            authorization=auth_context,
        )

        return Response(AttemptEvaluationReviewSerializer(evaluation).data, status=status.HTTP_200_OK)


class AttemptCancelView(APIView):
    """
    Cancel an attempt (active or submitted with pending result).
    Superadmin-only access.
    """

    permission_classes = [IsSuperadminOnly]

    @extend_schema(
        summary="Cancel an attempt",
        description="Cancels an active or submitted pending attempt with a recorded reason. Marks attempt result VOID.",
        request=CancelAttemptRequestSerializer,
        responses={
            200: AttemptReviewSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not eligible for cancellation"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Superadmin role required"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not found"),
        },
        tags=["Attempts"],
    )
    def post(self, request, attempt_id):
        serializer = CancelAttemptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_context = get_authorization_context(request.user)
        attempt, _ = cancel_attempt(
            attempt_id=attempt_id,
            reason=serializer.validated_data["reason"],
            authorization=auth_context,
        )

        attempt = (
            Attempt.objects.filter(id=attempt.id)
            .prefetch_related(
                "items__response__choices",
                "items__response__matches",
                "items__evaluation",
                "result__section_results",
            )
            .first()
        )
        return Response(AttemptReviewSerializer(attempt).data, status=status.HTTP_200_OK)


class AttemptReviewView(APIView):
    """
    Superadmin full review of an attempt.
    Includes item evaluations, student answers, and scores.
    """

    permission_classes = [IsSuperadminOnly]

    @extend_schema(
        summary="Review an attempt",
        description="Retrieves complete attempt details with student responses, evaluations, and results for Superadmin auditing.",
        responses={
            200: AttemptReviewSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Superadmin role required"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Attempt not found"),
        },
        tags=["Attempts"],
    )
    def get(self, request, attempt_id):
        attempt = (
            Attempt.objects.filter(id=attempt_id)
            .prefetch_related(
                "items__response__choices",
                "items__response__matches",
                "items__evaluation",
                "result__section_results",
            )
            .first()
        )
        if attempt is None:
            raise AttemptNotFoundError(f"Attempt '{attempt_id}' was not found.")

        return Response(AttemptReviewSerializer(attempt).data, status=status.HTTP_200_OK)
