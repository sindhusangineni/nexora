from rest_framework import serializers

from apps.assessment.models import AssessmentSection


class AssessmentSectionSerializer(serializers.ModelSerializer):
    """
    Representation of an AssessmentSection.
    """

    class Meta:
        model = AssessmentSection
        fields = [
            "id",
            "assessment_id",
            "title",
            "description",
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


class AssessmentSectionCreateRequestSerializer(serializers.Serializer):
    """
    Request serializer for adding a section to an Assessment.
    """

    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    position = serializers.IntegerField(min_value=0, default=0)
