from rest_framework import serializers

from apps.attempts.models import Attempt, AttemptResultStatus


class AttemptHistorySummarySerializer(serializers.ModelSerializer):
    """
    Compact summary representation of an Attempt for student history listing.
    Never exposes internal choices, answer keys, or question delivery payloads.
    Includes scorecard summary if evaluation has completed.
    """

    result_status = serializers.SerializerMethodField(
        help_text="Evaluation status of the attempt result (PENDING, FINAL, VOID) or null if active.",
    )
    score = serializers.SerializerMethodField(
        help_text="Finalized total score achieved, or null if pending/unfinalized.",
    )
    maximum_score = serializers.SerializerMethodField(
        help_text="Maximum total marks achievable on this attempt paper.",
    )
    percentage = serializers.SerializerMethodField(
        help_text="Finalized percentage score, or null if pending/unfinalized.",
    )
    total_questions = serializers.SerializerMethodField(
        help_text="Total questions on the attempt paper, or null if no result generated.",
    )
    attempted_questions = serializers.SerializerMethodField(
        help_text="Count of answered questions, or null if no result generated.",
    )

    class Meta:
        model = Attempt
        fields = [
            "id",
            "assessment_paper_id",
            "attempt_number",
            "status",
            "started_at",
            "submitted_at",
            "expires_at",
            "submission_reason",
            "result_status",
            "score",
            "maximum_score",
            "percentage",
            "total_questions",
            "attempted_questions",
        ]
        read_only_fields = fields

    def get_result_status(self, obj: Attempt) -> str | None:
        result = getattr(obj, "result", None)
        return result.status if result else None

    def get_score(self, obj: Attempt) -> str | None:
        result = getattr(obj, "result", None)
        if result and result.status == AttemptResultStatus.FINAL:
            return str(result.score)
        return None

    def get_maximum_score(self, obj: Attempt) -> str | None:
        result = getattr(obj, "result", None)
        if result and result.status in (AttemptResultStatus.FINAL, AttemptResultStatus.PENDING):
            return str(result.maximum_score)
        return None

    def get_percentage(self, obj: Attempt) -> str | None:
        result = getattr(obj, "result", None)
        if result and result.status == AttemptResultStatus.FINAL:
            return str(result.percentage)
        return None

    def get_total_questions(self, obj: Attempt) -> int | None:
        result = getattr(obj, "result", None)
        if result:
            return result.total_questions
        return None

    def get_attempted_questions(self, obj: Attempt) -> int | None:
        result = getattr(obj, "result", None)
        if result:
            return result.attempted_questions
        return None
