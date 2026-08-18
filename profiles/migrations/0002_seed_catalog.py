from django.db import migrations


SUBJECTS = (
    ("Mathématiques", "mathematiques"),
    ("Français", "francais"),
    ("Anglais", "anglais"),
    ("Physique", "physique"),
    ("Chimie", "chimie"),
    ("Biologie et sciences", "biologie-sciences"),
    ("Informatique et bureautique", "informatique-bureautique"),
    ("Programmation", "programmation"),
    ("Comptabilité et gestion", "comptabilite-gestion"),
    ("Statistiques et méthodologie", "statistiques-methodologie"),
)
LEVELS = (
    ("Primaire", "primaire", 1),
    ("Secondaire", "secondaire", 2),
    ("Humanités", "humanites", 3),
    ("Supérieur et universitaire", "superieur-universitaire", 4),
    ("Professionnel et certifications", "professionnel-certifications", 5),
)
MODES = (
    ("En ligne", "en-ligne"),
    ("À domicile", "a-domicile"),
    ("Lieu public", "lieu-public"),
    ("Centre de formation", "centre-formation"),
)
AREAS = (
    "Bandalungwa", "Barumbu", "Bumbu", "Gombe", "Kalamu", "Kasa-Vubu",
    "Kimbanseke", "Kinshasa", "Kintambo", "Kisenso", "Lemba", "Limete",
    "Lingwala", "Makala", "Maluku", "Masina", "Matete", "Mont-Ngafula",
    "Ndjili", "Ngaba", "Ngaliema", "Ngiri-Ngiri", "Nsele", "Selembao",
)


def seed_catalog(apps, schema_editor):
    subject_model = apps.get_model("profiles", "Subject")
    level_model = apps.get_model("profiles", "Level")
    mode_model = apps.get_model("profiles", "TeachingMode")
    area_model = apps.get_model("profiles", "ServiceArea")
    for name, slug in SUBJECTS:
        subject_model.objects.get_or_create(name=name, defaults={"slug": slug})
    for name, code, order in LEVELS:
        level_model.objects.get_or_create(name=name, defaults={"code": code, "order": order})
    for name, code in MODES:
        mode_model.objects.get_or_create(name=name, defaults={"code": code})
    for name in AREAS:
        area_model.objects.get_or_create(name=name, defaults={"slug": name.lower().replace("'", "-").replace(" ", "-")})


class Migration(migrations.Migration):
    dependencies = [("profiles", "0001_initial")]
    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
