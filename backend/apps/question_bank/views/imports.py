from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.question_bank.application import (
    execute_question_import,
    generate_csv_template,
    preview_question_import,
)
from apps.question_bank.permissions import IsSuperadminOnly
from apps.question_bank.serializers import (
    QuestionImportExecuteResponseSerializer,
    QuestionImportExecuteSerializer,
    QuestionImportFileSerializer,
    QuestionImportPreviewResponseSerializer,
)
from shared.api.errors import ErrorResponseSerializer


@extend_schema(
    tags=["Question Bank - Imports"],
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
        status.HTTP_409_CONFLICT: ErrorResponseSerializer,
    },
)
class QuestionImportViewSet(viewsets.ViewSet):
    """
    Administrative API for parsing, previewing, validating, and bulk-importing
    UPSC examination questions into the Question Bank as DRAFT records.
    Requires Superadmin privileges.
    """

    permission_classes = [IsSuperadminOnly]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Preview bulk question CSV import",
        description=(
            "Parses and validates an uploaded CSV file containing questions without persisting changes. "
            "Returns validation summaries, row-level errors, duplicate alerts, and formatted row previews."
        ),
        request=QuestionImportFileSerializer,
        responses={
            status.HTTP_200_OK: QuestionImportPreviewResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
    )
    def preview(self, request):
        serializer = QuestionImportFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        file_content = uploaded_file.read()

        try:
            result = preview_question_import(file_content)
            return Response(result, status=status.HTTP_200_OK)
        except DjangoValidationError as exc:
            return Response(
                {
                    "error": {
                        "code": "IMPORT_STRUCTURAL_ERROR",
                        "message": str(exc.message if hasattr(exc, "message") else exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Execute bulk question CSV import",
        description=(
            "Atomically validates and imports questions from an uploaded CSV file. "
            "Option A (All-or-Nothing): If any row contains a validation error, the entire batch is rejected. "
            "Questions are created strictly with DRAFT status using existing domain rules."
        ),
        request=QuestionImportExecuteSerializer,
        responses={
            status.HTTP_201_CREATED: QuestionImportExecuteResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
    )
    def execute(self, request):
        serializer = QuestionImportExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        skip_duplicates = serializer.validated_data.get("skip_duplicates", True)
        file_content = uploaded_file.read()

        try:
            result = execute_question_import(file_content, skip_duplicates=skip_duplicates)
            return Response(result, status=status.HTTP_201_CREATED)
        except DjangoValidationError as exc:
            msg = exc.message if hasattr(exc, "message") else str(exc)
            return Response(
                {
                    "error": {
                        "code": "IMPORT_VALIDATION_ERROR",
                        "message": msg,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Download bulk question CSV template",
        description="Generates and streams a downloadable standard CSV template with sample rows for all six question types.",
        responses={
            (status.HTTP_200_OK, "text/csv"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description="CSV template document",
            ),
        },
    )
    def template(self, request):
        csv_text = generate_csv_template()
        response = HttpResponse(csv_text, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="nexora_upsc_question_import_template.csv"'
        return response
