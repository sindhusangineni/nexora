from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.identity.permissions.roles import (
    ROLE_STUDENT,
    ROLE_SUPERADMIN,
    IsSuperadmin,
)


class IsSuperadminOnly(BasePermission):
    """
    Permission allowing exclusively members of the Superadmin group.
    Direct superusers without the Superadmin group are rejected.
    """

    def has_permission(self, request, view):
        return IsSuperadmin().has_permission(request, view)


class IsSuperadminOrStudentReadOnly(BasePermission):
    """
    Permission allowing:
    - Safe methods (GET, HEAD, OPTIONS): authenticated users with Student or Superadmin group.
    - Mutating methods (POST, PATCH, DELETE): exclusively users with Superadmin group.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return request.user.groups.filter(
                name__in=[ROLE_STUDENT, ROLE_SUPERADMIN]
            ).exists()
        return IsSuperadmin().has_permission(request, view)
