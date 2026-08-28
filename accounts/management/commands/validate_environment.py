import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Valide les variables requises pour l'environnement Django courant."

    def handle(self, *args, **options):
        environment = os.getenv("DJANGO_ENV", "development")
        required_settings = {
            "DJANGO_SECRET_KEY": settings.SECRET_KEY,
            "DJANGO_ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
            "POSTGRES_DB": settings.DATABASES["default"].get("NAME"),
            "POSTGRES_USER": settings.DATABASES["default"].get("USER"),
            "POSTGRES_PASSWORD": settings.DATABASES["default"].get("PASSWORD"),
            "PAYMENT_PROVIDER": settings.PAYMENT_PROVIDER,
            "PAYMENT_WEBHOOK_SECRET": settings.PAYMENT_WEBHOOK_SECRET,
            "PAYMENT_COMMISSION_RATE": settings.PAYMENT_COMMISSION_RATE,
        }
        missing = [name for name, value in required_settings.items() if not value]
        if missing:
            raise CommandError(f"Configuration {environment} incomplète : {', '.join(missing)}.")

        if environment in {"staging", "production"} and settings.DEBUG:
            raise CommandError(f"DEBUG doit être désactivé en {environment}.")

        self.stdout.write(self.style.SUCCESS(f"Configuration {environment} valide."))
