from decimal import Decimal
from rest_framework import serializers

from apps.attempts.models import AttemptResult, AttemptSectionResult


class AttemptSectionResultSerializer(serializers.ModelSerializer):
    """Result snapshot for an assessment section."""

    section_name = serializers.CharField(source="section_title_snapshot", read_only=True)
    question_count = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = AttemptSectionResult
        fields = [
            "id",
            "assessment_section_id",
            "section_name",
            "section_title_snapshot",
            "section_order_snapshot",
            "score",
            "maximum_score",
            "percentage",
            "question_count",
            "attempted_questions",
            "correct_questions",
            "incorrect_questions",
            "partially_correct_questions",
            "unanswered_questions",
            "pending_evaluation_questions",
        ]
        read_only_fields = fields

    def get_question_count(self, obj) -> int:
        return (
            (obj.attempted_questions or 0)
            + (obj.unanswered_questions or 0)
            + (obj.pending_evaluation_questions or 0)
        )

    def get_percentage(self, obj) -> str:
        if obj.maximum_score and obj.maximum_score > Decimal("0.00"):
            pct = (obj.score / obj.maximum_score * 100).quantize(Decimal("0.01"))
            return str(pct)
        return "0.00"


class AttemptResultSerializer(serializers.ModelSerializer):
    """
    Scorecard representation for students and superadmins.
    When status is PENDING, reflects that evaluation is underway.
    """

    assessment_paper_id = serializers.UUIDField(source="attempt.assessment_paper_id", read_only=True)
    attempt_number = serializers.IntegerField(source="attempt.attempt_number", read_only=True)
    attempt_status = serializers.CharField(source="attempt.status", read_only=True)
    result_status = serializers.CharField(source="status", read_only=True)
    submission_reason = serializers.CharField(source="attempt.submission_reason", read_only=True)
    started_at = serializers.DateTimeField(source="attempt.started_at", read_only=True)
    submitted_at = serializers.DateTimeField(source="attempt.submitted_at", read_only=True)
    section_results = AttemptSectionResultSerializer(many=True, read_only=True)

    class Meta:
        model = AttemptResult
        fields = [
            "id",
            "attempt_id",
            "assessment_paper_id",
            "attempt_number",
            "attempt_status",
            "result_status",
            "status",
            "submission_reason",
            "started_at",
            "submitted_at",
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

