from django.db import migrations, models

import verification.models
import verification.storage


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0003_verificationdecision"),
    ]

    operations = [
        migrations.AlterField(
            model_name="identityverification",
            name="document",
            field=models.FileField(
                storage=verification.storage.PrivateDocumentStorage(),
                upload_to=verification.models.private_document_path,
                validators=[verification.validators.validate_document],
            ),
        ),
        migrations.AlterField(
            model_name="professionalcredential",
            name="document",
            field=models.FileField(
                storage=verification.storage.PrivateDocumentStorage(),
                upload_to=verification.models.private_document_path,
                validators=[verification.validators.validate_document],
            ),
        ),
        migrations.AlterField(
            model_name="verificationupload",
            name="chunk_file",
            field=models.FileField(
                storage=verification.storage.PrivateDocumentStorage(),
                upload_to=verification.models.upload_chunk_path,
            ),
        ),
    ]
