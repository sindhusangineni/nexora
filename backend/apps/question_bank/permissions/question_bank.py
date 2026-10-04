from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.identity.permissions.roles import (
    ROLE_STUDENT,
    ROLE_SUPERADMIN,
    IsSuperadmin,
)


class IsSuperadminOrStudentReadOnly(BasePermission):
    """
    Authorization policy for Question Bank:
    - Anonymous requests: rejected with 401 Unauthorized.
    - Read requests (GET, HEAD, OPTIONS): allowed for authenticated users with Student or Superadmin role.
    - Write requests (POST, PATCH, DELETE): allowed exclusively for users with Superadmin role.
    - Strictly group-based; is_superuser is NOT an application-role bypass.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return request.user.groups.filter(
                name__in=[ROLE_STUDENT, ROLE_SUPERADMIN]
            ).exists()

        return IsSuperadmin().has_permission(request, view)


class IsSuperadminOnly(BasePermission):
    """
    Permission allowing only Superadmin group members.
    Used for lifecycle action endpoints and authoring mutations.
    """

    def has_permission(self, request, view):
        return IsSuperadmin().has_permission(request, view)
