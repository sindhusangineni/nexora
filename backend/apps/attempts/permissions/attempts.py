from rest_framework.permissions import BasePermission

from apps.identity.permissions.roles import (
    ROLE_STUDENT,
    ROLE_SUPERADMIN,
    IsStudent,
    IsSuperadmin,
)


class IsSuperadminOnly(BasePermission):
    """
    Permission allowing exclusively members of the Superadmin group.
    Direct superusers without the Superadmin group are rejected.
    """

    def has_permission(self, request, view):
        return IsSuperadmin().has_permission(request, view)


class IsStudentOnly(BasePermission):
    """
    Permission allowing exclusively members of the Student group.
    """

    def has_permission(self, request, view):
        return IsStudent().has_permission(request, view)


class IsStudentOrSuperadmin(BasePermission):
    """
    Permission allowing authenticated users with either Student or Superadmin group.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.groups.filter(
            name__in=[ROLE_STUDENT, ROLE_SUPERADMIN]
        ).exists()
