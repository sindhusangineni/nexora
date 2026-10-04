from rest_framework import serializers

from apps.learning.models import Chapter, Topic
from apps.learning.validators import normalize_name


class TopicSerializer(serializers.ModelSerializer):
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all())
    description = serializers.CharField(required=False, allow_blank=True, default="")
    position = serializers.IntegerField(min_value=0, default=0, required=False)

    class Meta:
        model = Topic
        fields = [
            "id",
            "chapter",
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
        chapter = attrs.get("chapter", getattr(self.instance, "chapter", None))
        name = attrs.get("name", getattr(self.instance, "name", None))

        if chapter and name:
            qs = Topic.objects.filter(chapter=chapter, name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": ["A topic with this name already exists under this chapter."]}
                )
        return attrs
