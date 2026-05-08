# Data migration: role groups aligned with the documented RBAC matrix.

from django.db import migrations
from django.db.models import Q


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    owner, _ = Group.objects.get_or_create(name="Owner")
    manager, _ = Group.objects.get_or_create(name="Manager")
    tailor, _ = Group.objects.get_or_create(name="Tailor")
    staff, _ = Group.objects.get_or_create(name="Staff")

    all_perms = list(Permission.objects.all())
    owner.permissions.set(all_perms)
    manager.permissions.set(all_perms)

    tailor_perms = Permission.objects.filter(
        Q(content_type__app_label="customers", codename__startswith="view_")
        | Q(
            content_type__app_label="orders",
            codename__in=[
                "view_order",
                "view_orderitem",
                "view_measurement",
                "view_material",
                "view_orderitemmaterial",
            ],
        )
        | Q(
            content_type__app_label="production",
            codename__in=[
                "view_ticket",
                "change_ticket",
                "add_statushistory",
                "view_statushistory",
                "view_productionstage",
                "view_employee",
                "view_delivery",
            ],
        )
    )
    tailor.permissions.set(tailor_perms)

    staff_perms = Permission.objects.filter(
        Q(content_type__app_label="customers")
        | Q(content_type__app_label="orders"),
    ).exclude(
        codename__startswith="delete_",
    )
    staff.permissions.set(staff_perms)


class Migration(migrations.Migration):

    dependencies = [
        ("production", "0002_seed_production_stages"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_groups, migrations.RunPython.noop),
    ]
