from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("learning", "0007_learningrequest_learning_request_complete_time_slot")]

    operations = [
        migrations.AddField(
            model_name="proposal",
            name="availability",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="learningevent",
            name="name",
            field=models.CharField(
                choices=[
                    ("request.created", "Demande créée"),
                    ("match.created", "Matching créé"),
                    ("proposal.sent", "Proposition envoyée"),
                    ("proposal.accepted", "Proposition acceptée"),
                    ("proposal.rejected", "Proposition refusée"),
                    ("booking.created", "Réservation créée"),
                    ("session.completed", "Session terminée"),
                    ("review.created", "Avis créé"),
                    ("payment.completed", "Paiement terminé"),
                ],
                max_length=30,
            ),
        ),
    ]