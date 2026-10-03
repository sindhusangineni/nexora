from rest_framework import serializers

from apps.learning.models import Domain
from apps.learning.validators import normalize_name


class DomainSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = Domain
        fields = [
            "id",
            "name",
            "description",
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
        name = attrs.get("name")
        if name:
            qs = Domain.objects.filter(name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": ["A domain with this name already exists."]}
                )
        return attrs
