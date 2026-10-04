from rest_framework import serializers

from apps.attempts.models.enums import EvaluationState


class StartAttemptRequestSerializer(serializers.Serializer):
    """Request payload to start or resume an attempt."""

    assessment_paper_id = serializers.UUIDField(required=True)


class SaveResponseRequestSerializer(serializers.Serializer):
    """Request payload to record or update a student response."""

    choice_id = serializers.UUIDField(required=False, allow_null=True)
    selected_choice_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    boolean_response = serializers.BooleanField(required=False, allow_null=True)
    assertion_reason_response = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    match_pairs = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )
    text_response = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class EvaluateDescriptiveRequestSerializer(serializers.Serializer):
    """Request payload for Superadmin descriptive evaluation."""

    evaluation_state = serializers.ChoiceField(
        choices=[
            EvaluationState.CORRECT,
            EvaluationState.INCORRECT,
            EvaluationState.PARTIALLY_CORRECT,
        ],
        required=True,
    )
    marks_awarded = serializers.DecimalField(
        max_digits=8,
        decimal_places=4,
        required=False,
        allow_null=True,
        min_value=0,
    )
    marks_deducted = serializers.DecimalField(
        max_digits=8,
        decimal_places=4,
        required=False,
        allow_null=True,
        min_value=0,
    )
    evaluation_comments = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class CancelAttemptRequestSerializer(serializers.Serializer):
    """Request payload to cancel an attempt."""

    reason = serializers.CharField(
        required=True,
        min_length=1,
        trim_whitespace=True,
    )
