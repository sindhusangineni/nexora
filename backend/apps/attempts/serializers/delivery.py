from rest_framework import serializers

from apps.attempts.models import (
    Attempt,
    AttemptItem,
    AttemptItemChoice,
    AttemptResponse,
)


class AttemptItemChoiceDeliverySerializer(serializers.ModelSerializer):
    """Safe delivery presentation of question choices."""

    class Meta:
        model = AttemptItemChoice
        fields = [
            "id",
            "choice_id",
            "presented_position",
        ]
        read_only_fields = fields


class AttemptResponseDeliverySerializer(serializers.ModelSerializer):
    """Safe delivery state of the student's current response."""

    selected_choice_ids = serializers.SerializerMethodField()
    selected_matches = serializers.SerializerMethodField()

    class Meta:
        model = AttemptResponse
        fields = [
            "id",
            "answer_state",
            "boolean_response",
            "assertion_reason_response",
            "text_response",
            "selected_choice_ids",
            "selected_matches",
        ]
        read_only_fields = fields

    def get_selected_choice_ids(self, obj: AttemptResponse) -> list[str]:
        return [str(c.choice_id) for c in obj.choices.all()]

    def get_selected_matches(self, obj: AttemptResponse) -> list[dict]:
        return [
            {
                "left_item_id": str(m.left_item_id),
                "right_item_id": str(m.right_item_id),
            }
            for m in obj.matches.all()
        ]


class AttemptItemDeliverySerializer(serializers.ModelSerializer):
    """
    Delivery-safe representation of an AttemptItem.
    NEVER exposes correct answers, answer keys, explanations, or marking internals.
    """

    choices = AttemptItemChoiceDeliverySerializer(many=True, read_only=True)
    response = AttemptResponseDeliverySerializer(read_only=True)

    class Meta:
        model = AttemptItem
        fields = [
            "id",
            "paper_item_id",
            "assessment_section_id",
            "presentation_order",
            "allocated_marks",
            "allocated_penalty",
            "choices",
            "response",
        ]
        read_only_fields = fields


class AttemptDeliverySerializer(serializers.ModelSerializer):
    """
    Delivery-safe representation of an Attempt for the student frontend.
    """

    items = AttemptItemDeliverySerializer(many=True, read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id",
            "student_id",
            "assessment_paper_id",
            "attempt_number",
            "duration_seconds",
            "started_at",
            "expires_at",
            "submitted_at",
            "status",
            "items",
        ]
        read_only_fields = fields
