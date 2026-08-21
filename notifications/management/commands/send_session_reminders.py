from django.core.management.base import BaseCommand

from notifications.services import send_due_session_reminders


class Command(BaseCommand):
    help = "Envoie les rappels des sessions confirmées prévues dans 24 h ou 1 h."

    def handle(self, *args, **options):
        sent_count = send_due_session_reminders()
        self.stdout.write(self.style.SUCCESS(f"{sent_count} rappel(s) envoyé(s)."))
