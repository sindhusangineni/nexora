from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.adapters.question_bank import DatabaseQuestionBankCandidateAdapter
from apps.assessment.application.generate_paper import generate_paper
from apps.assessment.exceptions import PaperNotFoundError
from apps.assessment.models import AssessmentPaper
from apps.assessment.serializers import AssessmentPaperSerializer
from shared.api.errors import ErrorResponseSerializer


class GeneratePaperView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Generate an assessment paper",
        description="Generates an immutable test paper from a PUBLISHED assessment definition.",
        request=None,
        responses={
            201: AssessmentPaperSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description="Generation error or insufficient questions"),
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Assessment not found"),
        },
        tags=["Assessment"],
    )
    def post(self, request, assessment_id):
        adapter = DatabaseQuestionBankCandidateAdapter()
        paper = generate_paper(
            assessment_id=assessment_id,
            question_bank_port=adapter,
        )
        return Response(AssessmentPaperSerializer(paper).data, status=status.HTTP_201_CREATED)


class AssessmentPaperDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve an assessment paper",
        description="Retrieves a generated assessment paper and its frozen items.",
        responses={
            200: AssessmentPaperSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication required"),
            404: OpenApiResponse(response=ErrorResponseSerializer, description="Paper not found"),
        },
        tags=["Assessment"],
    )
    def get(self, request, paper_id):
        paper = (
            AssessmentPaper.objects.filter(id=paper_id)
            .prefetch_related("items__assessment_section")
            .first()
        )
        if not paper:
            raise PaperNotFoundError("Assessment paper not found.")
        return Response(AssessmentPaperSerializer(paper).data, status=status.HTTP_200_OK)
