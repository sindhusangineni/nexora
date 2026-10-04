import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory

from apps.identity.permissions.roles import (
    ROLE_STUDENT,
    ROLE_SUPERADMIN,
    IsStudent,
    IsSuperadmin,
    get_user_roles,
)
from apps.identity.services.registration import RegistrationService

User = get_user_model()


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.mark.django_db
class TestRBAC:
    def test_registration_assigns_student_group(self):
        user = RegistrationService().register_user(
            email="student.rbac@example.com",
            password="StrongPassword123!",
        )

        assert Group.objects.filter(name=ROLE_STUDENT).exists()
        assert user.groups.filter(name=ROLE_STUDENT).exists()
        assert not user.groups.filter(name=ROLE_SUPERADMIN).exists()
        assert not user.is_staff
        assert not user.is_superuser

        roles = get_user_roles(user)
        assert roles == ["student"]

    def test_normal_user_is_not_superadmin(self, factory):
        user = RegistrationService().register_user(
            email="normal@example.com",
            password="StrongPassword123!",
        )
        request = factory.get("/")
        request.user = user

        is_student_perm = IsStudent()
        is_superadmin_perm = IsSuperadmin()

        assert is_student_perm.has_permission(request, None) is True
        assert is_superadmin_perm.has_permission(request, None) is False

    def test_superadmin_has_superadmin_permission(self, factory):
        user = User.objects.create_superuser(
            email="superadmin@example.com",
            password="StrongPassword123!",
        )
        superadmin_group, _ = Group.objects.get_or_create(name=ROLE_SUPERADMIN)
        user.groups.add(superadmin_group)

        request = factory.get("/")
        request.user = user

        is_superadmin_perm = IsSuperadmin()
        assert is_superadmin_perm.has_permission(request, None) is True

        roles = get_user_roles(user)
        assert "superadmin" in roles

    def test_superuser_without_superadmin_group_does_not_have_superadmin_permission(self, factory):
        """
        Verify that is_superuser=True alone does NOT grant the Nexora Superadmin application role.
        Nexora RBAC strictly requires membership in the Superadmin Django Group.
        """
        user = User.objects.create_superuser(
            email="superuser.only@example.com",
            password="StrongPassword123!",
        )
        # Note: user is superuser, but NOT in Superadmin group
        assert user.is_superuser is True
        assert not user.groups.filter(name=ROLE_SUPERADMIN).exists()

        request = factory.get("/")
        request.user = user

        is_superadmin_perm = IsSuperadmin()
        assert is_superadmin_perm.has_permission(request, None) is False

        roles = get_user_roles(user)
        assert "superadmin" not in roles
