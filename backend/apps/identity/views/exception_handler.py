from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import exceptions, status
from rest_framework.response import Response


from apps.identity.exceptions import (
    IdentityAPIException,
    InvalidCredentialsException,
    InvalidTokenException,
)



def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if isinstance(exc, IdentityAPIException):
        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
            status=exc.status_code,
        )

    if response is not None:
        if isinstance(exc, exceptions.ValidationError):
            fields = {}
            non_field_errors = []

            if isinstance(response.data, dict):
                for key, val in response.data.items():
                    messages = [str(m) for m in val] if isinstance(val, list) else [str(val)]
                    if key in ("non_field_errors", "detail"):
                        non_field_errors.extend(messages)
                    else:
                        fields[key] = messages
            elif isinstance(response.data, list):
                non_field_errors = [str(m) for m in response.data]

            message = "Please correct the highlighted fields."
            if non_field_errors and not fields:
                message = " ".join(non_field_errors)

            error_payload = {
                "code": "VALIDATION_ERROR",
                "message": message,
            }
            if fields:
                error_payload["fields"] = fields

            response.data = {"error": error_payload}

        elif isinstance(exc, exceptions.AuthenticationFailed):
            detail_msg = str(exc.detail) if hasattr(exc, "detail") else "Authentication failed."
            response.data = {
                "error": {
                    "code": getattr(exc, "default_code", "AUTHENTICATION_FAILED").upper(),
                    "message": detail_msg,
                }
            }

        elif isinstance(exc, exceptions.NotAuthenticated):
            response.data = {
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication credentials were not provided.",
                }
            }

        elif isinstance(exc, exceptions.PermissionDenied):
            response.data = {
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "You do not have permission to perform this action.",
                }
            }

        else:
            code = getattr(exc, "default_code", "API_ERROR").upper()
            msg = str(response.data.get("detail", response.data)) if isinstance(response.data, dict) else str(response.data)
            response.data = {
                "error": {
                    "code": code,
                    "message": msg,
                }
            }

    return response
