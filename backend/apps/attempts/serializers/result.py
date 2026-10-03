from rest_framework import serializers

from apps.attempts.models import AttemptResult, AttemptSectionResult


class AttemptSectionResultSerializer(serializers.ModelSerializer):
    """Result snapshot for an assessment section."""

    class Meta:
        model = AttemptSectionResult
        fields = [
            "id",
            "assessment_section_id",
            "section_title_snapshot",
            "section_order_snapshot",
            "score",
            "maximum_score",
            "attempted_questions",
            "correct_questions",
            "incorrect_questions",
            "partially_correct_questions",
            "unanswered_questions",
            "pending_evaluation_questions",
        ]
        read_only_fields = fields


class AttemptResultSerializer(serializers.ModelSerializer):
    """
    Scorecard representation for students and superadmins.
    When status is PENDING, reflects that evaluation is underway.
    """

    section_results = AttemptSectionResultSerializer(many=True, read_only=True)

    class Meta:
        model = AttemptResult
        fields = [
            "id",
            "attempt_id",
            "status",
            "score",
            "maximum_score",
            "percentage",
            "total_questions",
            "attempted_questions",
            "correct_questions",
            "incorrect_questions",
            "partially_correct_questions",
            "unanswered_questions",
            "pending_evaluation_questions",
            "finalized_at",
            "section_results",
        ]
        read_only_fields = fields
