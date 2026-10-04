from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.application.lifecycle import archive_assessment, publish_assessment
from apps.assessment.exceptions import (
    AssessmentImmutableError,
    AssessmentNotFoundError,
)
from apps.assessment.models import Assessment, AssessmentStatus
from apps.assessment.permissions import (
    IsSuperadminOnly,
    IsSuperadminOrStudentReadOnly,
)
from apps.assessment.serializers import (
    AssessmentCreateRequestSerializer,
    AssessmentSerializer,
    AssessmentUpdateRequestSerializer,
)
from apps.identity.permissions.roles import ROLE_SUPERADMIN
from shared.api.errors import ErrorResponseSerializer


class AssessmentListCreateView(APIView):
    permission_classes = [IsSuperadminOrStudentReadOnly]

    @extend_schema(
        summary="List assessments",
        description="Students see only PUBLISHED assessments; Superadmins see all.",
        responses={
            200: AssessmentSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
        },
        tags=["Assessment"],
    )
    def get(self, request):
        user = request.user
        qs = Assessment.objects.all().order_by("-created_at")
        is_admin = user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists()
        if not is_admin:
            qs = qs.filter(status=AssessmentStatus.PUBLISHED)
        serializer = AssessmentSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create an assessment",
        description="Creates a new assessment definition in DRAFT status. Superadmin only.",
        request=AssessmentCreateRequestSerializer,
        responses={
            201: AssessmentSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Validation error"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
        },
        tags=["Assessment"],
    )
    def post(self, request):
        serializer = AssessmentCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assessment = Assessment.objects.create(
            status=AssessmentStatus.DRAFT,
            **serializer.validated_data,
        )
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)


class AssessmentDetailView(APIView):
    permission_classes = [IsSuperadminOrStudentReadOnly]

    def _get_assessment(self, request, assessment_id) -> Assessment:
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found.")

        user = request.user
        is_admin = user.is_authenticated and user.groups.filter(name=ROLE_SUPERADMIN).exists()
        if not is_admin and assessment.status != AssessmentStatus.PUBLISHED:
            raise AssessmentNotFoundError("Assessment not found.")
        return assessment

    @extend_schema(
        summary="Retrieve an assessment",
        description="Students can only retrieve PUBLISHED assessments; Superadmins can retrieve any.",
        responses={
            200: AssessmentSerializer,
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Not found"),
        },
        tags=["Assessment"],
    )
    def get(self, request, assessment_id):
        assessment = self._get_assessment(request, assessment_id)
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update an assessment",
        description="Updates an assessment in DRAFT status. Superadmin only.",
        request=AssessmentUpdateRequestSerializer,
        responses={
            200: AssessmentSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Validation error"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Not found"),
        },
        tags=["Assessment"],
    )
    def patch(self, request, assessment_id):
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found.")

        if not assessment.can_edit():
            raise AssessmentImmutableError(
                f"Cannot update assessment in '{assessment.status}' status (must be DRAFT)."
            )

        serializer = AssessmentUpdateRequestSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for key, val in serializer.validated_data.items():
            setattr(assessment, key, val)
        assessment.save()
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_200_OK)


class AssessmentPublishView(APIView):
    permission_classes = [IsSuperadminOnly]

    @extend_schema(
        summary="Publish an assessment",
        description="Transitions an assessment from DRAFT to PUBLISHED. Superadmin only.",
        request=None,
        responses={
            200: AssessmentSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Validation or transition error"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Not found"),
        },
        tags=["Assessment"],
    )
    def post(self, request, assessment_id):
        assessment = publish_assessment(assessment_id)
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_200_OK)


class AssessmentArchiveView(APIView):
    permission_classes = [IsSuperadminOnly]

    @extend_schema(
        summary="Archive an assessment",
        description="Transitions an assessment from PUBLISHED to ARCHIVED. Superadmin only.",
        request=None,
        responses={
            200: AssessmentSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Invalid status transition"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Not found"),
        },
        tags=["Assessment"],
    )
    def post(self, request, assessment_id):
        assessment = archive_assessment(assessment_id)
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_200_OK)
