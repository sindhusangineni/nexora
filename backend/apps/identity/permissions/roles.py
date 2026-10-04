from rest_framework.permissions import BasePermission

ROLE_STUDENT = "Student"
ROLE_SUPERADMIN = "Superadmin"


def get_user_roles(user) -> list[str]:
    if not user or not user.is_authenticated:
        return []
    roles = list(user.groups.values_list("name", flat=True))
    return [role.lower() for role in roles]


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name=ROLE_STUDENT).exists()
        )


class IsSuperadmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name=ROLE_SUPERADMIN).exists()
        )
