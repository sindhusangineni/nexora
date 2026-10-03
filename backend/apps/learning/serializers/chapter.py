from rest_framework import serializers

from apps.learning.models import Chapter, Subject
from apps.learning.validators import normalize_name


class ChapterSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    description = serializers.CharField(required=False, allow_blank=True, default="")
    position = serializers.IntegerField(min_value=0, default=0, required=False)

    class Meta:
        model = Chapter
        fields = [
            "id",
            "subject",
            "name",
            "description",
            "position",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value: str) -> str:
        clean = normalize_name(value)
        if not clean:
            raise serializers.ValidationError("Name cannot be blank.")
        return clean

    def validate(self, attrs):
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        name = attrs.get("name", getattr(self.instance, "name", None))

        if subject and name:
            qs = Chapter.objects.filter(subject=subject, name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": ["A chapter with this name already exists under this subject."]}
                )
        return attrs
