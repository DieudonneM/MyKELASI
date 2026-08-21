import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0002_session_and_terminal_statuses"),
        ("learning", "0004_learningevent_session_completed"),
        ("messaging", "0001_initial"),
        ("profiles", "0002_seed_catalog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="conversation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="messaging.conversation",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="booking",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="bookings.booking",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="proposal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="learning.proposal",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="teacher_profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="profiles.teacherprofile",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(conversation__isnull=False)
                    | models.Q(teacher_profile__isnull=False)
                    | models.Q(proposal__isnull=False)
                    | models.Q(booking__isnull=False)
                ),
                name="report_has_target",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.CheckConstraint(
                condition=~(
                    models.Q(conversation__isnull=False, teacher_profile__isnull=False)
                    | models.Q(conversation__isnull=False, proposal__isnull=False)
                    | models.Q(conversation__isnull=False, booking__isnull=False)
                    | models.Q(teacher_profile__isnull=False, proposal__isnull=False)
                    | models.Q(teacher_profile__isnull=False, booking__isnull=False)
                    | models.Q(proposal__isnull=False, booking__isnull=False)
                ),
                name="report_has_single_target",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.CheckConstraint(
                condition=models.Q(message__isnull=True)
                | models.Q(conversation__isnull=False),
                name="report_message_requires_conversation",
            ),
        ),
    ]