from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.identity.permissions.roles import (
    ROLE_STUDENT,
    ROLE_SUPERADMIN,
    IsSuperadmin,
)


class IsSuperadminOrReadOnlyAuthenticated(BasePermission):
    """
    Authorization policy for the Learning domain:
    - Anonymous requests: rejected with 401 Unauthorized.
    - Read requests (GET, HEAD, OPTIONS): allowed for authenticated users with Student or Superadmin role.
    - Write requests (POST, PATCH, DELETE): allowed exclusively for users with Superadmin role.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return request.user.groups.filter(
                name__in=[ROLE_STUDENT, ROLE_SUPERADMIN]
            ).exists()

        return IsSuperadmin().has_permission(request, view)
