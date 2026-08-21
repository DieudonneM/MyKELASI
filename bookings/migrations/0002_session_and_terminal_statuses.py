import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "En attente"),
                    ("CONFIRMED", "Confirmée"),
                    ("REJECTED", "Refusée"),
                    ("CANCELLED", "Annulée"),
                    ("COMPLETED", "Terminée"),
                    ("NO_SHOW", "Absence"),
                    ("DISPUTED", "Contestée"),
                ],
                default="PENDING",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="bookingtransition",
            name="from_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("PENDING", "En attente"),
                    ("CONFIRMED", "Confirmée"),
                    ("REJECTED", "Refusée"),
                    ("CANCELLED", "Annulée"),
                    ("COMPLETED", "Terminée"),
                    ("NO_SHOW", "Absence"),
                    ("DISPUTED", "Contestée"),
                ],
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="bookingtransition",
            name="to_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "En attente"),
                    ("CONFIRMED", "Confirmée"),
                    ("REJECTED", "Refusée"),
                    ("CANCELLED", "Annulée"),
                    ("COMPLETED", "Terminée"),
                    ("NO_SHOW", "Absence"),
                    ("DISPUTED", "Contestée"),
                ],
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("learner_present_at", models.DateTimeField(blank=True, null=True)),
                ("teacher_present_at", models.DateTimeField(blank=True, null=True)),
                ("actual_started_at", models.DateTimeField(blank=True, null=True)),
                ("actual_ended_at", models.DateTimeField(blank=True, null=True)),
                ("outcome", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "booking",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="session",
                        to="bookings.booking",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="session",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(actual_ended_at__isnull=True)
                    | models.Q(actual_started_at__isnull=True)
                    | models.Q(actual_ended_at__gte=models.F("actual_started_at"))
                ),
                name="session_end_not_before_start",
            ),
        ),
    ]