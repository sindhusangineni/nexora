from decimal import Decimal
from rest_framework import serializers

from apps.assessment.models import Assessment, AssessmentStatus, AssessmentType


class AssessmentSerializer(serializers.ModelSerializer):
    """
    Representation of an Assessment definition.
    """

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "description",
            "type",
            "status",
            "duration_seconds",
            "marks_per_question",
            "penalty_per_question",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]


class AssessmentCreateRequestSerializer(serializers.Serializer):
    """
    Request serializer for creating a new Assessment specification in DRAFT status.
    """

    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    type = serializers.ChoiceField(
        choices=AssessmentType.choices,
        default=AssessmentType.PRACTICE,
    )
    duration_seconds = serializers.IntegerField(
        min_value=1,
        default=3600,
        help_text="Configured duration in seconds (must be >= 1).",
    )
    marks_per_question = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.01"),
        default=Decimal("2.00"),
        help_text="Marks awarded per correct answer.",
    )
    penalty_per_question = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.00"),
        default=Decimal("0.66"),
        help_text="Penalty deducted per incorrect answer.",
    )


class AssessmentUpdateRequestSerializer(serializers.Serializer):
    """
    Request serializer for updating an Assessment in DRAFT status.
    """

    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=AssessmentType.choices, required=False)
    duration_seconds = serializers.IntegerField(min_value=1, required=False)
    marks_per_question = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
    )
    penalty_per_question = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
    )
