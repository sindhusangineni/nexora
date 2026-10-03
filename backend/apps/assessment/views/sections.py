from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.exceptions import (
    AssessmentImmutableError,
    AssessmentNotFoundError,
    SectionNotFoundError,
)
from apps.assessment.models import Assessment, AssessmentSection
from apps.assessment.permissions import (
    IsSuperadminOnly,
    IsSuperadminOrStudentReadOnly,
)
from apps.assessment.serializers import (
    AssessmentSectionCreateRequestSerializer,
    AssessmentSectionSerializer,
)
from shared.api.errors import ErrorResponseSerializer


class AssessmentSectionListCreateView(APIView):
    permission_classes = [IsSuperadminOrStudentReadOnly]

    @extend_schema(
        summary="List sections for an assessment",
        responses={
            200: AssessmentSectionSerializer(many=True),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Assessment not found"),
        },
        tags=["Assessment"],
    )
    def get(self, request, assessment_id):
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found.")

        sections = assessment.sections.all().order_by("position", "created_at")
        return Response(AssessmentSectionSerializer(sections, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a section in an assessment",
        description="Allowed only while assessment is in DRAFT status. Superadmin only.",
        request=AssessmentSectionCreateRequestSerializer,
        responses={
            201: AssessmentSectionSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Validation error"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Assessment not found"),
        },
        tags=["Assessment"],
    )
    def post(self, request, assessment_id):
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found.")

        if not assessment.can_edit():
            raise AssessmentImmutableError(
                f"Cannot add sections to assessment in '{assessment.status}' status."
            )

        serializer = AssessmentSectionCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        section = AssessmentSection.objects.create(
            assessment=assessment,
            **serializer.validated_data,
        )
        return Response(AssessmentSectionSerializer(section).data, status=status.HTTP_201_CREATED)


class AssessmentSectionDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsSuperadminOnly()]
        return [IsSuperadminOrStudentReadOnly()]

    @extend_schema(
        summary="Retrieve an assessment section",
        responses={
            200: AssessmentSectionSerializer,
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Section not found"),
        },
        tags=["Assessment"],
    )
    def get(self, request, section_id):
        section = AssessmentSection.objects.filter(id=section_id).first()
        if not section:
            raise SectionNotFoundError("Assessment section not found.")
        return Response(AssessmentSectionSerializer(section).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete an assessment section",
        description="Allowed only while assessment is in DRAFT status. Superadmin only.",
        responses={
            204: OpenApiResponse(description="Deleted successfully"),
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Immutable assessment error"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Section not found"),
        },
        tags=["Assessment"],
    )
    def delete(self, request, section_id):
        section = AssessmentSection.objects.filter(id=section_id).first()
        if not section:
            raise SectionNotFoundError("Assessment section not found.")

        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
