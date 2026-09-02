from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("profiles", "0004_configurationversion")]

    operations = [
        migrations.AddField(
            model_name="servicearea",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[MinValueValidator(-90), MaxValueValidator(90)],
                verbose_name="latitude du centre de zone",
            ),
        ),
        migrations.AddField(
            model_name="servicearea",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                validators=[MinValueValidator(-180), MaxValueValidator(180)],
                verbose_name="longitude du centre de zone",
            ),
        ),
    ]