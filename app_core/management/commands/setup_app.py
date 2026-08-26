from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Exécute les migrations et vérifications de déploiement de manière reproductible."

    def handle(self, *args, **options):
        self.stdout.write("Migration de la base de données...")
        call_command("migrate", interactive=False)
        self.stdout.write(self.style.SUCCESS("Migrations exécutées avec succès."))
