from rest_framework import exceptions, serializers, status


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


class ApplicationAPIException(exceptions.APIException):
    """
    Base API exception for application-level domain errors adhering to the
    standardized Nexora error envelope: {"error": {"code": ..., "message": ...}}.
    """

    def __init__(
        self,
        code="ERROR",
        message="An error occurred.",
        status_code=status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(detail=message)
