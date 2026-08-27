from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial"), ("learning", "0007_proposal_availability_events")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="booking",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications", to="bookings.booking",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="proposal",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications", to="learning.proposal",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("SESSION_REMINDER_24H", "Rappel de session 24 h"),
                    ("SESSION_REMINDER_1H", "Rappel de session 1 h"),
                    ("PROPOSAL_ACCEPTED", "Proposition acceptée"),
                    ("PROPOSAL_REJECTED", "Proposition refusée"),
                ],
                max_length=32,
            ),
        ),
    ]