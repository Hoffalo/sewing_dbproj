# Data migration: canonical production pipeline for Costuras Lucía.

from django.db import migrations


def seed_stages(apps, schema_editor):
    ProductionStage = apps.get_model("production", "ProductionStage")
    rows = [
        ("RECEIVED", 1, False),
        ("DESIGN_CONFIRMED", 2, False),
        ("CUTTING", 3, False),
        ("SEWING", 4, False),
        ("FINISHING", 5, False),
        ("QUALITY_CHECK", 6, False),
        ("READY", 7, False),
        ("DELIVERED", 8, True),
    ]
    for name, sequence, is_terminal in rows:
        ProductionStage.objects.update_or_create(
            name=name,
            defaults={"sequence": sequence, "is_terminal": is_terminal},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("production", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_stages, migrations.RunPython.noop),
    ]
