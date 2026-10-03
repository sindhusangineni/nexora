from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text="Standardized machine-readable error code."
    )
    message = serializers.CharField(
        help_text="Human-readable explanation of the error."
    )
    fields = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False,
        help_text="Field-level validation error details when applicable.",
    )


class ErrorResponseSerializer(serializers.Serializer):
    error = ErrorDetailSerializer(
        help_text="Error envelope containing standardized error details."
    )
