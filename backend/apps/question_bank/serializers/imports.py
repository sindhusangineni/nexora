from rest_framework import serializers

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class QuestionImportFileSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text="CSV file containing bulk questions to parse and preview (max 5 MB, up to 500 rows)."
    )

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("A valid file must be uploaded.")

        if value.size > MAX_UPLOAD_SIZE_BYTES:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            )

        name = value.name.lower() if value.name else ""
        if not (name.endswith(".csv") or name.endswith(".txt")):
            raise serializers.ValidationError("File must be a CSV format document (.csv).")

        # Deep content verification: do not trust filename or MIME type alone
        try:
            content_bytes = value.read()
            value.seek(0)
        except Exception as e:
            raise serializers.ValidationError(f"Unable to read uploaded file content: {str(e)}")

        # Check for null bytes (typical indicator of binary/executable payload)
        if b"\x00" in content_bytes:
            raise serializers.ValidationError(
                "Uploaded file contains binary content or null bytes. Only valid UTF-8 CSV text files are supported."
            )

        # Verify file is strictly decodable as UTF-8 or UTF-8-sig
        decoded_text = None
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                decoded_text = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            raise serializers.ValidationError(
                "Uploaded file cannot be decoded. File content must be valid UTF-8 text."
            )

        return value


class QuestionImportExecuteSerializer(QuestionImportFileSerializer):
    skip_duplicates = serializers.BooleanField(
        default=True,
        required=False,
        help_text="When true, rows identified as duplicates are safely skipped. When false, duplicates abort the import.",
    )


class RowValidationErrorSerializer(serializers.Serializer):
    row_number = serializers.IntegerField(help_text="Row index in the uploaded CSV (1-indexed).")
    field = serializers.CharField(help_text="Column name associated with the error.")
    message = serializers.CharField(help_text="Descriptive error explanation.")
    raw_data = serializers.DictField(required=False, help_text="Raw row values for context.")


class ParsedRowPreviewSerializer(serializers.Serializer):
    row_number = serializers.IntegerField()
    is_valid = serializers.BooleanField()
    is_duplicate = serializers.BooleanField()
    duplicate_type = serializers.CharField(allow_null=True, required=False)
    duplicate_reason = serializers.CharField(allow_null=True)
    question_type = serializers.CharField(allow_null=True)
    text = serializers.CharField()
    difficulty = serializers.CharField(allow_null=True)
    topic_name = serializers.CharField(allow_blank=True, required=False)
    topic_id = serializers.CharField(allow_null=True, required=False)
    source_type = serializers.CharField(allow_null=True, required=False)
    source_year = serializers.IntegerField(allow_null=True, required=False)
    external_question_id = serializers.CharField(allow_null=True, required=False)
    errors = serializers.ListField(child=serializers.CharField())


class QuestionImportPreviewResponseSerializer(serializers.Serializer):
    total_rows = serializers.IntegerField(help_text="Total data rows parsed from the CSV.")
    valid_rows = serializers.IntegerField(help_text="Number of valid, non-duplicate rows ready for import.")
    invalid_rows = serializers.IntegerField(help_text="Number of rows with validation or structural errors.")
    duplicate_rows = serializers.IntegerField(help_text="Number of rows matching existing questions or repeated in the file.")
    can_import = serializers.BooleanField(help_text="True if there are zero invalid rows.")
    summary = serializers.DictField(child=serializers.IntegerField(), help_text="Breakdown of rows by question_type.")
    errors = RowValidationErrorSerializer(many=True, help_text="List of all row-level validation errors.")
    rows = ParsedRowPreviewSerializer(many=True, help_text="Row-by-row previews for tabular review.")


class QuestionImportExecuteResponseSerializer(serializers.Serializer):
    total_rows = serializers.IntegerField(help_text="Total rows processed.")
    imported_rows = serializers.IntegerField(help_text="Number of questions successfully created as DRAFT.")
    skipped_rows = serializers.IntegerField(help_text="Number of duplicate questions skipped.")
    failed_rows = serializers.IntegerField(help_text="Number of failed questions.")
    created_question_ids = serializers.ListField(child=serializers.CharField(), help_text="UUIDs of created questions.")
    errors = serializers.ListField(child=serializers.CharField(), help_text="Any execution errors if applicable.")
