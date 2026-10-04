import getpass
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Seed or ensure a Superadmin user and role in the platform idempotently."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email address for the superadmin account.",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Password for the superadmin account.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for input; read credentials from environment or arguments.",
        )

    def handle(self, *args, **options):
        email = options.get("email") or os.environ.get("NEXORA_SUPERADMIN_EMAIL")
        password = options.get("password") or os.environ.get("NEXORA_SUPERADMIN_PASSWORD")
        no_input = options.get("no_input", False)

        if not email:
            if no_input:
                raise CommandError(
                    "Superadmin email must be provided via --email or NEXORA_SUPERADMIN_EMAIL when using --no-input."
                )
            email = input("Superadmin Email: ").strip()

        if not email:
            raise CommandError("Email address cannot be empty.")

        email = email.strip().lower()

        if not password:
            if no_input:
                raise CommandError(
                    "Superadmin password must be provided via --password or NEXORA_SUPERADMIN_PASSWORD when using --no-input."
                )
            password = getpass.getpass("Superadmin Password: ")
            password_confirm = getpass.getpass("Confirm Superadmin Password: ")
            if password != password_confirm:
                raise CommandError("Passwords do not match.")

        if not password:
            raise CommandError("Password cannot be empty.")

        superadmin_group, _ = Group.objects.get_or_create(name="Superadmin")
        Group.objects.get_or_create(name="Student")

        user = User.objects.filter(email=email).first()

        if user:
            user.is_staff = True
            user.is_superuser = True
            user.email_verified = True
            if options.get("password") or os.environ.get("NEXORA_SUPERADMIN_PASSWORD"):
                user.set_password(password)
            user.save()
            user.groups.add(superadmin_group)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superadmin user '{email}' already exists. Ensured superadmin privileges and group assignment."
                )
            )
        else:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True,
                email_verified=True,
            )
            user.groups.add(superadmin_group)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created Superadmin user '{email}' and assigned to Superadmin group."
                )
            )
