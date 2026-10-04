from io import StringIO
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
class TestSeedSuperadminCommand:
    def test_seed_superadmin_creates_user_and_group(self):
        out = StringIO()
        call_command(
            "seed_superadmin",
            email="admin@example.com",
            password="AdminPassword123!",
            no_input=True,
            stdout=out,
        )

        output = out.getvalue()
        assert "Successfully created Superadmin user" in output

        user = User.objects.get(email="admin@example.com")
        assert user.check_password("AdminPassword123!")
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.email_verified is True

        superadmin_group = Group.objects.get(name="Superadmin")
        assert superadmin_group in user.groups.all()

    def test_seed_superadmin_is_idempotent(self):
        out1 = StringIO()
        call_command(
            "seed_superadmin",
            email="admin@example.com",
            password="AdminPassword123!",
            no_input=True,
            stdout=out1,
        )

        out2 = StringIO()
        call_command(
            "seed_superadmin",
            email="admin@example.com",
            password="AdminPassword123!",
            no_input=True,
            stdout=out2,
        )

        output2 = out2.getvalue()
        assert "already exists. Ensured superadmin privileges" in output2
        assert User.objects.filter(email="admin@example.com").count() == 1
