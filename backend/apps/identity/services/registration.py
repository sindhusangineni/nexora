from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

User = get_user_model()


class RegistrationService:
    @transaction.atomic
    def register_user(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        user = User.objects.create_user(email=normalized_email, password=password)

        student_group, _ = Group.objects.get_or_create(name="Student")
        user.groups.add(student_group)

        return user
