"""
Global exception handler for DRF requests.
Re-exported from shared.api.exception_handler.
"""
from apps.identity.exceptions import (
    IdentityAPIException,
    InvalidCredentialsException,
    InvalidTokenException,
)
from shared.api.exception_handler import custom_exception_handler

__all__ = [
    "IdentityAPIException",
    "InvalidCredentialsException",
    "InvalidTokenException",
    "custom_exception_handler",
]
