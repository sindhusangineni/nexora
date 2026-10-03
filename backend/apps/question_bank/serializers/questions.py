from rest_framework import serializers

from apps.question_bank.models.enums import (
    Difficulty,
    QuestionSourceType,
    QuestionType,
)
from apps.question_bank.serializers.content import (
    AssertionReasonContentRequestSerializer,
    ChoiceItemRequestSerializer,
    DescriptiveContentRequestSerializer,
    MatchFollowingContentRequestSerializer,
    TrueFalseContentRequestSerializer,
)


class BaseQuestionPayloadSerializer(serializers.Serializer):
    """
    Base request serializer for question and version creation payloads.
    Enforces strict typing and mutual exclusivity of type-specific content.
    """

    text = serializers.CharField(
        required=True,
        min_length=1,
        help_text="Primary question stem or prompt text.",
    )
    question_type = serializers.ChoiceField(
        choices=QuestionType.choices,
        required=True,
        help_text="Canonical question type.",
    )
    difficulty = serializers.ChoiceField(
        choices=Difficulty.choices,
        required=True,
        help_text="Standardized difficulty rating.",
    )
    explanation = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Pedagogical explanation for the correct answer.",
    )
    topic_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text="List of Learning Topic UUIDs to associate.",
    )

    # Provenance metadata (Phase 1.1)
    source_type = serializers.ChoiceField(
        choices=QuestionSourceType.choices,
        required=False,
        allow_null=True,
        help_text="Origin classification of this editorial content.",
    )
    source_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="Human-readable origin source name.",
    )
    source_reference = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=512,
        help_text="Citation, examination paper reference, or contributor identifier.",
    )
    source_year = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1000,
        max_value=2100,
        help_text="Four-digit calendar year associated with the source.",
    )
    external_question_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="External system or question dataset identifier.",
    )

    # Explicit type-specific content payloads
    choices = serializers.ListField(
        child=ChoiceItemRequestSerializer(),
        required=False,
        help_text="Choice list for MCQ and MULTIPLE_SELECT questions.",
    )
    true_false = TrueFalseContentRequestSerializer(
        required=False,
        help_text="Boolean content for TRUE_FALSE questions.",
    )
    assertion_reason = AssertionReasonContentRequestSerializer(
        required=False,
        help_text="Assertion, reason, and relationship for ASSERTION_REASON questions.",
    )
    match_following = MatchFollowingContentRequestSerializer(
        required=False,
        help_text="Left items, right items, and pairs for MATCH_FOLLOWING questions.",
    )
    descriptive = DescriptiveContentRequestSerializer(
        required=False,
        help_text="Marks and expected rubric for DESCRIPTIVE questions.",
    )

    def validate_text(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Question text cannot be blank.")
        return value.strip()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        q_type = attrs.get("question_type")

        # Mutually exclusive content mapping
        content_fields = {
            "choices": attrs.get("choices"),
            "true_false": attrs.get("true_false"),
            "assertion_reason": attrs.get("assertion_reason"),
            "match_following": attrs.get("match_following"),
            "descriptive": attrs.get("descriptive"),
        }

        expected_field = {
            QuestionType.MCQ: "choices",
            QuestionType.MULTIPLE_SELECT: "choices",
            QuestionType.TRUE_FALSE: "true_false",
            QuestionType.ASSERTION_REASON: "assertion_reason",
            QuestionType.MATCH_FOLLOWING: "match_following",
            QuestionType.DESCRIPTIVE: "descriptive",
        }.get(q_type)

        if not expected_field:
            raise serializers.ValidationError(
                {"question_type": [f"Unsupported question type: '{q_type}'."]}
            )

        # Check that required content is supplied
        if content_fields.get(expected_field) is None:
            raise serializers.ValidationError(
                {expected_field: [f"Content for question type '{q_type}' is required."]}
            )

        # Check that extraneous content fields are NOT supplied
        extraneous = [
            f for f, val in content_fields.items() if f != expected_field and val is not None
        ]
        if extraneous:
            raise serializers.ValidationError(
                {
                    "question_type": [
                        f"Cannot supply extraneous content fields {extraneous} for question_type '{q_type}'."
                    ]
                }
            )

        return attrs


class QuestionCreateSerializer(BaseQuestionPayloadSerializer):
    """
    Request serializer for creating a new Question aggregate root and its initial version.
    """
    pass


class QuestionVersionCreateSerializer(BaseQuestionPayloadSerializer):
    """
    Request serializer for creating a new editorial version for an existing Question.
    topic_ids is optional; if omitted, the existing QuestionTopic associations are preserved.
    """

    topic_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=None,
        help_text="Optional list of Topic UUIDs. If omitted, existing question topics are preserved.",
    )


class QuestionVersionPatchSerializer(serializers.Serializer):
    """
    Request serializer for partially updating a DRAFT QuestionVersion.
    Rejects modification of version_number, status, question_type, or question identity.
    """

    text = serializers.CharField(
        required=False,
        min_length=1,
        help_text="Updated question prompt text.",
    )
    difficulty = serializers.ChoiceField(
        choices=Difficulty.choices,
        required=False,
        help_text="Updated difficulty level.",
    )
    explanation = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Updated explanation.",
    )
    topic_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=None,
        help_text="Optional list of Topic UUIDs to update on the question.",
    )

    # Provenance metadata
    source_type = serializers.ChoiceField(
        choices=QuestionSourceType.choices,
        required=False,
        allow_null=True,
    )
    source_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
    )
    source_reference = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=512,
    )
    source_year = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1000,
        max_value=2100,
    )
    external_question_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
    )

    # Content updates
    choices = serializers.ListField(
        child=ChoiceItemRequestSerializer(),
        required=False,
    )
    true_false = TrueFalseContentRequestSerializer(required=False)
    assertion_reason = AssertionReasonContentRequestSerializer(required=False)
    match_following = MatchFollowingContentRequestSerializer(required=False)
    descriptive = DescriptiveContentRequestSerializer(required=False)

    def validate_text(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Question text cannot be blank.")
        return value.strip()

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Disallow prohibited fields
        initial_data = getattr(self, "initial_data", {})
        if "version_number" in initial_data:
            raise serializers.ValidationError(
                {"version_number": ["version_number is immutable and generated by the server."]}
            )
        if "status" in initial_data:
            raise serializers.ValidationError(
                {"status": ["status cannot be modified via PATCH. Use the dedicated lifecycle endpoints."]}
            )
        if "question_type" in initial_data:
            raise serializers.ValidationError(
                {"question_type": ["question_type cannot be changed on an existing version."]}
            )
        if "question" in initial_data or "question_id" in initial_data:
            raise serializers.ValidationError(
                {"question": ["Question identity cannot be modified."]}
            )

        return attrs
