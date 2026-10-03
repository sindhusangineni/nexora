from django.db.models.deletion import ProtectedError
from rest_framework import status
from shared.api.errors import ApplicationAPIException


class ProtectedResourceException(ApplicationAPIException):
    def __init__(
        self,
        message="Cannot delete this resource because it is referenced by other active resources.",
    ):
        super().__init__(
            code="PROTECTED_RESOURCE",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


def delete_curriculum_resource(instance) -> None:
    """
    Attempt deletion of a curriculum model instance directly via instance.delete().
    Relies on Django ORM models.PROTECT foreign key behavior to raise ProtectedError
    when dependent child records exist, and translates ProtectedError into an
    API-compliant 409 Conflict (PROTECTED_RESOURCE) exception.
    Does not perform separate pre-flight child count checks.
    """
    try:
        instance.delete()
    except ProtectedError as exc:
        model_name = instance._meta.verbose_name
        raise ProtectedResourceException(
            f"Cannot delete {model_name} because it is referenced by active child resources. "
            f"Delete or reassign child resources first."
        ) from exc
