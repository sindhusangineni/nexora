from rest_framework import serializers

from apps.assessment.models import (
    Difficulty,
    QuestionType,
    ScopeType,
    SelectionRule,
)


class SelectionRuleSerializer(serializers.ModelSerializer):
    """
    Representation of a SelectionRule.
    """

    class Meta:
        model = SelectionRule
        fields = [
            "id",
            "assessment_id",
            "assessment_section_id",
            "scope_type",
            "scope_id",
            "question_type",
            "difficulty",
            "question_count",
            "position",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assessment_id",
            "created_at",
            "updated_at",
        ]


class SelectionRuleCreateRequestSerializer(serializers.Serializer):
    """
    Request serializer for adding a selection rule to an Assessment.
    """

    assessment_section_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Optional section UUID within the assessment.",
    )
    scope_type = serializers.ChoiceField(choices=ScopeType.choices)
    scope_id = serializers.UUIDField(help_text="Scalar UUID of Domain/Subject/Chapter/Topic.")
    question_type = serializers.ChoiceField(
        choices=QuestionType.choices,
        required=False,
        allow_null=True,
        default=None,
    )
    difficulty = serializers.ChoiceField(
        choices=Difficulty.choices,
        required=False,
        allow_null=True,
        default=None,
    )
    question_count = serializers.IntegerField(
        min_value=1,
        help_text="Number of questions to select (must be >= 1).",
    )
    position = serializers.IntegerField(min_value=0, default=0)
