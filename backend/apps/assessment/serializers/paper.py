from rest_framework import serializers

from apps.assessment.models import AssessmentPaper, AssessmentPaperItem


class AssessmentPaperItemSerializer(serializers.ModelSerializer):
    """
    Representation of an individual frozen paper item.
    """

    class Meta:
        model = AssessmentPaperItem
        fields = [
            "id",
            "paper_id",
            "question_id",
            "question_version_id",
            "assessment_section_id",
            "presentation_order",
            "allocated_marks",
            "allocated_penalty",
            "created_at",
        ]
        read_only_fields = fields


class AssessmentPaperSerializer(serializers.ModelSerializer):
    """
    Representation of a generated, immutable AssessmentPaper.
    """

    items = AssessmentPaperItemSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentPaper
        fields = [
            "id",
            "assessment_id",
            "status",
            "duration_seconds",
            "marks_per_question",
            "penalty_per_question",
            "created_at",
            "items",
        ]
        read_only_fields = fields
