from rest_framework import serializers

from apps.attempts.models import AttemptEvaluation
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


class QuestionTaxonomySerializer(serializers.Serializer):
    domain = serializers.CharField(allow_blank=True, required=False)
    subject = serializers.CharField(allow_blank=True, required=False)
    chapter = serializers.CharField(allow_blank=True, required=False)
    topic = serializers.CharField(allow_blank=True, required=False)


class QuestionReviewItemChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    text = serializers.CharField()
    position = serializers.IntegerField()
    is_correct = serializers.BooleanField(required=False, allow_null=True)


class StudentQuestionReviewItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    paper_item_id = serializers.UUIDField()
    assessment_section_id = serializers.UUIDField(allow_null=True)
    section_name = serializers.CharField(allow_blank=True)
    question_id = serializers.UUIDField()
    question_version_id = serializers.UUIDField()
    question_number = serializers.IntegerField()
    presentation_order = serializers.IntegerField()
    question_type = serializers.CharField()
    question_text = serializers.CharField()
    taxonomy = QuestionTaxonomySerializer(allow_null=True, required=False)
    allocated_marks = serializers.CharField()
    allocated_penalty = serializers.CharField()
    is_answered = serializers.BooleanField()
    answer_state = serializers.CharField()
    evaluation_status = serializers.CharField()
    marks_awarded = serializers.CharField(allow_null=True)
    explanation = serializers.CharField(allow_null=True, required=False)
    choices = QuestionReviewItemChoiceSerializer(many=True, required=False)
    assertion = serializers.CharField(allow_blank=True, required=False)
    reason = serializers.CharField(allow_blank=True, required=False)
    left_items = serializers.ListField(child=serializers.DictField(), required=False)
    right_items = serializers.ListField(child=serializers.DictField(), required=False)
    candidate_answer = serializers.DictField(allow_null=True, required=False)
    correct_answer = serializers.DictField(allow_null=True, required=False)


class AdminQuestionReviewItemSerializer(StudentQuestionReviewItemSerializer):
    is_evaluable = serializers.BooleanField(default=False)
    response = AttemptResponseDeliverySerializer(allow_null=True, required=False)
    evaluation = AttemptEvaluationReviewSerializer(allow_null=True, required=False)


class StudentAttemptReviewSerializer(serializers.Serializer):
    """Student-safe attempt review containing only authorized scorecard and review details."""

    id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    assessment_paper_id = serializers.UUIDField()
    attempt_number = serializers.IntegerField()
    status = serializers.CharField()
    result_status = serializers.CharField()
    submission_reason = serializers.CharField(allow_null=True)
    duration_seconds = serializers.IntegerField()
    started_at = serializers.DateTimeField()
    submitted_at = serializers.DateTimeField(allow_null=True)
    items = StudentQuestionReviewItemSerializer(many=True)
    result = AttemptResultSerializer(allow_null=True)


class AdminAttemptReviewSerializer(serializers.Serializer):
    """Complete attempt review for Superadmin auditing and descriptive grading."""

    id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    assessment_paper_id = serializers.UUIDField()
    attempt_number = serializers.IntegerField()
    status = serializers.CharField()
    result_status = serializers.CharField()
    submission_reason = serializers.CharField(allow_null=True)
    duration_seconds = serializers.IntegerField()
    started_at = serializers.DateTimeField()
    submitted_at = serializers.DateTimeField(allow_null=True)
    expires_at = serializers.DateTimeField()
    cancelled_at = serializers.DateTimeField(allow_null=True, required=False)
    cancelled_by = serializers.UUIDField(allow_null=True, required=False)
    cancellation_reason = serializers.CharField(allow_null=True, required=False)
    items = AdminQuestionReviewItemSerializer(many=True)
    result = AttemptResultSerializer(allow_null=True)


# Backwards compatibility aliases
AttemptReviewSerializer = AdminAttemptReviewSerializer
AttemptItemReviewSerializer = AdminQuestionReviewItemSerializer

