from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid

import verification.models


class Migration(migrations.Migration):
    dependencies = [("verification", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="VerificationUpload",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("document_type", models.CharField(max_length=20)),
                ("title", models.CharField(blank=True, max_length=180)),
                ("institution", models.CharField(blank=True, max_length=180)),
                ("issued_year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("file_name", models.CharField(max_length=255)),
                ("file_size", models.PositiveIntegerField()),
                ("received_size", models.PositiveIntegerField(default=0)),
                ("chunk_file", models.FileField(upload_to=verification.models.upload_chunk_path)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]