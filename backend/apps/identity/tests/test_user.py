import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_with_normalized_lowercase_email(self):
        user = User.objects.create_user(email="Test.User@EXAMPLE.COM", password="securepassword123")
        assert user.email == "test.user@example.com"

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(email="test@example.com", password="securepassword123")
        assert user.check_password("securepassword123")
        assert user.password != "securepassword123"

    def test_create_user_rejects_missing_email(self):
        with pytest.raises(ValueError, match="The Email field must be set"):
            User.objects.create_user(email="", password="securepassword123")

    def test_normal_user_defaults(self):
        user = User.objects.create_user(email="test@example.com", password="securepassword123")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.email_verified is False

    def test_create_superuser_sets_required_flags(self):
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
        )
        assert admin_user.is_staff is True
        assert admin_user.is_superuser is True
        assert admin_user.is_active is True

    def test_create_superuser_rejects_is_staff_false(self):
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpassword123",
                is_staff=False,
            )

    def test_create_superuser_rejects_is_superuser_false(self):
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpassword123",
                is_superuser=False,
            )
