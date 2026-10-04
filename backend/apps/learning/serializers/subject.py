from rest_framework import serializers

from apps.learning.models import Domain, Subject
from apps.learning.validators import normalize_name


class SubjectSerializer(serializers.ModelSerializer):
    domain = serializers.PrimaryKeyRelatedField(queryset=Domain.objects.all())
    description = serializers.CharField(required=False, allow_blank=True, default="")
    position = serializers.IntegerField(min_value=0, default=0, required=False)

    class Meta:
        model = Subject
        fields = [
            "id",
            "domain",
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
        domain = attrs.get("domain", getattr(self.instance, "domain", None))
        name = attrs.get("name", getattr(self.instance, "name", None))

        if domain and name:
            qs = Subject.objects.filter(domain=domain, name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": ["A subject with this name already exists under this domain."]}
                )
        return attrs
