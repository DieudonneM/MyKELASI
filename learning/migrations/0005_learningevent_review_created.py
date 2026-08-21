from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("learning", "0004_learningevent_session_completed")]
    operations = [
        migrations.AlterField(
            model_name="learningevent",
            name="name",
            field=models.CharField(
                choices=[
                    ("request.created", "Demande créée"),
                    ("match.created", "Matching créé"),
                    ("proposal.sent", "Proposition envoyée"),
                    ("booking.created", "Réservation créée"),
                    ("session.completed", "Session terminée"),
                    ("review.created", "Avis créé"),
                ],
                max_length=30,
            ),
        )
    ]