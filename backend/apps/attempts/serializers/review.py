from rest_framework import serializers

from apps.attempts.models import (
    Attempt,
    AttemptEvaluation,
    AttemptItem,
)
from apps.attempts.serializers.delivery import AttemptResponseDeliverySerializer
from apps.attempts.serializers.result import AttemptResultSerializer


class AttemptEvaluationReviewSerializer(serializers.ModelSerializer):
    """Evaluation record details visible exclusively to Superadmin."""

    class Meta:
        model = AttemptEvaluation
        fields = [
            "id",
            "evaluation_state",
            "marks_awarded",
            "marks_deducted",
            "net_marks",
            "evaluator_id",
            "evaluated_at",
            "evaluation_comments",
        ]
        read_only_fields = fields


class AttemptItemReviewSerializer(serializers.ModelSerializer):
    """
    Superadmin view of an AttemptItem.
    Includes student response and detailed evaluation status/rubric.
    """

    response = AttemptResponseDeliverySerializer(read_only=True)
    evaluation = AttemptEvaluationReviewSerializer(read_only=True)

    class Meta:
        model = AttemptItem
        fields = [
            "id",
            "paper_item_id",
            "assessment_section_id",
            "question_id",
            "question_version_id",
            "presentation_order",
            "allocated_marks",
            "allocated_penalty",
            "response",
            "evaluation",
        ]
        read_only_fields = fields


class AttemptReviewSerializer(serializers.ModelSerializer):
    """
    Full attempt review representation for Superadmin.
    Includes items, responses, item-level evaluations, and scorecard.
    """

    items = AttemptItemReviewSerializer(many=True, read_only=True)
    result = AttemptResultSerializer(read_only=True)

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
            "submission_reason",
            "status",
            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",
            "items",
            "result",
        ]
        read_only_fields = fields
