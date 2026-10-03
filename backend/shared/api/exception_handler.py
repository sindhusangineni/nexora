from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from shared.api.errors import ApplicationAPIException


def custom_exception_handler(exc, context):
    """
    Standardized DRF exception handler enforcing Nexora's universal error envelope:
    {
        "error": {
            "code": "...",
            "message": "...",
            "fields": { ... }  # optional, for validation errors
        }
    }
    """
    response = drf_exception_handler(exc, context)

    # Domain / Application exceptions when not handled by default DRF handler
    if response is None:
        from apps.question_bank.exceptions import (
            ContentRepresentationError,
            ImmutableVersionError,
            InvalidStatusTransitionError,
            InvalidTopicError,
            PublicationConflictError,
            PublicationValidationError,
            QuestionBankError,
            VersionCreationConflictError,
        )
        from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
        from django.http import Http404

        if isinstance(exc, (PublicationConflictError, VersionCreationConflictError)):
            code = getattr(exc, "code", "CONFLICT")
            return Response(
                {
                    "error": {
                        "code": code,
                        "message": str(exc),
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        if isinstance(exc, (
            InvalidStatusTransitionError,
            ImmutableVersionError,
            PublicationValidationError,
            ContentRepresentationError,
            InvalidTopicError,
            QuestionBankError,
        )):
            code_map = {
                InvalidStatusTransitionError: "INVALID_STATUS_TRANSITION",
                ImmutableVersionError: "IMMUTABLE_VERSION",
                PublicationValidationError: "PUBLICATION_VALIDATION_ERROR",
                ContentRepresentationError: "CONTENT_REPRESENTATION_ERROR",
                InvalidTopicError: "INVALID_TOPIC",
                QuestionBankError: "QUESTION_BANK_ERROR",
            }
            code = code_map.get(type(exc), "QUESTION_BANK_ERROR")
            msg = str(exc)
            if hasattr(exc, "messages") and exc.messages:
                msg = " ".join(str(m) for m in exc.messages)
            return Response(
                {
                    "error": {
                        "code": code,
                        "message": msg,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(exc, DjangoValidationError):
            fields = {}
            non_field_errors = []
            if hasattr(exc, "message_dict"):
                for k, v in exc.message_dict.items():
                    fields[k] = [str(m) for m in v]
            elif hasattr(exc, "messages"):
                non_field_errors = [str(m) for m in exc.messages]
            msg = " ".join(non_field_errors) if non_field_errors else "Please correct the highlighted fields."
            payload = {"code": "VALIDATION_ERROR", "message": msg}
            if fields:
                payload["fields"] = fields
            return Response({"error": payload}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(exc, (ObjectDoesNotExist, Http404)):
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": str(exc) if str(exc) else "Resource not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # Application-level domain exceptions
    if isinstance(exc, ApplicationAPIException) or (
        hasattr(exc, "code")
        and hasattr(exc, "message")
        and hasattr(exc, "status_code")
        and isinstance(exc, exceptions.APIException)
    ):
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
                    messages = (
                        [str(m) for m in val]
                        if isinstance(val, list)
                        else [str(val)]
                    )
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
            detail_msg = (
                str(exc.detail)
                if hasattr(exc, "detail")
                else "Authentication failed."
            )
            response.data = {
                "error": {
                    "code": getattr(
                        exc, "default_code", "AUTHENTICATION_FAILED"
                    ).upper(),
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

        elif isinstance(exc, exceptions.PermissionDenied) or response.status_code == status.HTTP_403_FORBIDDEN:
            response.data = {
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "You do not have permission to perform this action.",
                }
            }

        elif isinstance(exc, exceptions.NotFound) or response.status_code == status.HTTP_404_NOT_FOUND:
            detail_msg = (
                str(response.data.get("detail", "Resource not found."))
                if isinstance(response.data, dict)
                else str(response.data)
            )
            response.data = {
                "error": {
                    "code": "NOT_FOUND",
                    "message": detail_msg,
                }
            }

        else:
            code = getattr(exc, "default_code", "API_ERROR").upper()
            msg = (
                str(response.data.get("detail", response.data))
                if isinstance(response.data, dict)
                else str(response.data)
            )
            response.data = {
                "error": {
                    "code": code,
                    "message": msg,
                }
            }

    return response
