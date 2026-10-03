from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.exceptions import (
    AssessmentImmutableError,
    AssessmentNotFoundError,
    AssessmentValidationError,
    SelectionRuleNotFoundError,
)
from apps.assessment.models import (
    Assessment,
    AssessmentSection,
    SelectionRule,
)
from apps.assessment.permissions import (
    IsSuperadminOnly,
    IsSuperadminOrStudentReadOnly,
)
from apps.assessment.serializers import (
    SelectionRuleCreateRequestSerializer,
    SelectionRuleSerializer,
)
from shared.api.errors import ErrorResponseSerializer


class SelectionRuleListCreateView(APIView):
    permission_classes = [IsSuperadminOrStudentReadOnly]

    @extend_schema(
        summary="List selection rules for an assessment",
        responses={
            200: SelectionRuleSerializer(many=True),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Assessment not found"),
        },
        tags=["Assessment"],
    )
    def get(self, request, assessment_id):
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found.")

        rules = assessment.selection_rules.all().order_by("position", "created_at")
        return Response(SelectionRuleSerializer(rules, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a selection rule for an assessment",
        description="Allowed only while assessment is in DRAFT status. Superadmin only.",
        request=SelectionRuleCreateRequestSerializer,
        responses={
            201: SelectionRuleSerializer,
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
                f"Cannot add selection rules to assessment in '{assessment.status}' status."
            )

        serializer = SelectionRuleCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        section_id = data.pop("assessment_section_id", None)
        section = None
        if section_id:
            section = AssessmentSection.objects.filter(id=section_id).first()
            if not section:
                raise AssessmentValidationError("Specified assessment section not found.")
            if section.assessment_id != assessment.id:
                raise AssessmentValidationError("Specified assessment section does not belong to this assessment.")

        rule = SelectionRule.objects.create(
            assessment=assessment,
            assessment_section=section,
            **data,
        )
        return Response(SelectionRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class SelectionRuleDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsSuperadminOnly()]
        return [IsSuperadminOrStudentReadOnly()]

    @extend_schema(
        summary="Retrieve a selection rule",
        responses={
            200: SelectionRuleSerializer,
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Rule not found"),
        },
        tags=["Assessment"],
    )
    def get(self, request, rule_id):
        rule = SelectionRule.objects.filter(id=rule_id).first()
        if not rule:
            raise SelectionRuleNotFoundError("Selection rule not found.")
        return Response(SelectionRuleSerializer(rule).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete a selection rule",
        description="Allowed only while assessment is in DRAFT status. Superadmin only.",
        responses={
            204: OpenApiResponse(description="Deleted successfully"),
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Immutable assessment error"),
            403: OpenApiResponse(response=ErrorResponseSerializer, description="Permission denied"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Rule not found"),
        },
        tags=["Assessment"],
    )
    def delete(self, request, rule_id):
        rule = SelectionRule.objects.filter(id=rule_id).first()
        if not rule:
            raise SelectionRuleNotFoundError("Selection rule not found.")

        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
