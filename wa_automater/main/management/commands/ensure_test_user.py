import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure a demo test user exists (configured via WA_DEMO_* env vars)."

    @staticmethod
    def _env_bool(name, default=False):
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def handle(self, *args, **options):
        username = os.getenv("WA_DEMO_USERNAME", "test_user").strip()
        password = os.getenv("WA_DEMO_PASSWORD", "test1234").strip()
        email = os.getenv("WA_DEMO_EMAIL", "testuser@example.local").strip()
        force_password_reset = self._env_bool("WA_DEMO_FORCE_PASSWORD_RESET", False)
        is_staff = self._env_bool("WA_DEMO_IS_STAFF", True)
        is_superuser = self._env_bool("WA_DEMO_IS_SUPERUSER", True)

        if not username:
            self.stdout.write(self.style.WARNING("Skipped: WA_DEMO_USERNAME is empty."))
            return

        if not password:
            self.stdout.write(self.style.WARNING("Skipped: WA_DEMO_PASSWORD is empty."))
            return

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )

        changed = False
        if created:
            if email and user.email != email:
                user.email = email
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            user.set_password(password)
            changed = True
        elif force_password_reset:
            user.set_password(password)
            changed = True

        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed = True

        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed = True

        if changed:
            user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}'."))
        elif force_password_reset:
            self.stdout.write(self.style.SUCCESS(f"Demo user '{username}' password was reset."))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Demo user '{username}' already exists (password unchanged, permissions synced)."
                )
            )