import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("bookings", "0002_session_and_terminal_statuses"),
        ("learning", "0004_learningevent_session_completed"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="conversation", to="bookings.booking")),
                ("learner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="learner_conversations", to=settings.AUTH_USER_MODEL)),
                ("learning_request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to="learning.learningrequest")),
                ("teacher", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="teacher_conversations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-last_message_at", "-created_at")},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("content", models.TextField(max_length=4000)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="messaging.conversation")),
            ],
            options={"ordering": ("created_at",)},
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("reason", models.CharField(choices=[("SPAM", "Spam"), ("HARASSMENT", "Harcèlement"), ("FRAUD", "Fraude"), ("INAPPROPRIATE", "Contenu inapproprié"), ("OTHER", "Autre")], max_length=20)),
                ("description", models.TextField(blank=True, max_length=2000)),
                ("status", models.CharField(choices=[("OPEN", "Ouvert"), ("IN_REVIEW", "En cours"), ("RESOLVED", "Résolu"), ("DISMISSED", "Classé")], default="OPEN", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="messaging.conversation")),
                ("message", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="messaging.message")),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="ReportAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("VIEWED", "Consulté"), ("IN_REVIEW", "Pris en charge"), ("RESOLVED", "Résolu"), ("DISMISSED", "Classé")], max_length=12)),
                ("note", models.TextField(blank=True, max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="report_actions", to=settings.AUTH_USER_MODEL)),
                ("report", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="actions", to="messaging.report")),
            ],
            options={"ordering": ("created_at",)},
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.UniqueConstraint(fields=("learning_request", "learner", "teacher"), name="unique_request_participant_conversation"),
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.CheckConstraint(condition=~models.Q(("learner", models.F("teacher"))), name="conversation_distinct_participants"),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["conversation", "created_at"], name="messaging_m_convers_2c54d4_idx"),
        ),
    ]