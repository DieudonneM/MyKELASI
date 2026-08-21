import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("bookings", "0002_session_and_terminal_statuses"),
        ("profiles", "0002_seed_catalog"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("punctuality", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("communication", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("quality", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("comment", models.TextField(blank=True, max_length=2000)),
                ("status", models.CharField(choices=[("PUBLISHED", "Publié"), ("HIDDEN", "Masqué")], default="PUBLISHED", max_length=10)),
                ("moderation_reason", models.TextField(blank=True, max_length=2000)),
                ("moderated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("moderated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="moderated_reviews", to=settings.AUTH_USER_MODEL)),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="authored_reviews", to=settings.AUTH_USER_MODEL)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reviews", to="bookings.session")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="received_reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="ReviewModerationAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("HIDDEN", "Masqué"), ("RESTORED", "Restauré")], max_length=10)),
                ("reason", models.TextField(max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_moderation_actions", to=settings.AUTH_USER_MODEL)),
                ("review", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_actions", to="reviews.review")),
            ],
            options={"ordering": ("created_at",)},
        ),
        migrations.CreateModel(
            name="ReviewResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField(max_length=2000)),
                ("is_hidden", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_responses", to=settings.AUTH_USER_MODEL)),
                ("review", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="response", to="reviews.review")),
            ],
        ),
        migrations.CreateModel(
            name="TrustScoreSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.CharField(max_length=20)),
                ("score", models.DecimalField(decimal_places=2, max_digits=5)),
                ("components", models.JSONField(default=dict)),
                ("input_counts", models.JSONField(default=dict)),
                ("source", models.CharField(max_length=40)),
                ("calculated_at", models.DateTimeField(auto_now_add=True)),
                ("teacher_profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trust_score_snapshots", to="profiles.teacherprofile")),
            ],
            options={"ordering": ("-calculated_at", "-pk")},
        ),
        migrations.AddConstraint(model_name="review", constraint=models.UniqueConstraint(fields=("session", "reviewer"), name="unique_reviewer_per_session")),
        migrations.AddConstraint(model_name="review", constraint=models.CheckConstraint(condition=~models.Q(("reviewer", models.F("subject"))), name="review_distinct_participants")),
    ]