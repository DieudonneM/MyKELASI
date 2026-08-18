from django.db import migrations

from accounts.roles import INTERNAL_ROLE_NAMES


def create_internal_roles(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    for role_name in INTERNAL_ROLE_NAMES:
        group_model.objects.get_or_create(name=role_name)


def remove_internal_roles(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    group_model.objects.filter(name__in=INTERNAL_ROLE_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_internal_roles, remove_internal_roles),
    ]
