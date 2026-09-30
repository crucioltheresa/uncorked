from django.db import migrations

GROUP_NAME = "Store Manager"
CODENAME = "access_dashboard"


def create_store_manager_group(apps, schema_editor):
    """
    Create the "Store Manager" group with the dashboard permission.
    Django normally adds permissions after all migrations have run, so on
    a new database the permission is created here first.
    """
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="dashboard", model="dashboardaccess"
    )
    permission, _ = Permission.objects.get_or_create(
        codename=CODENAME,
        content_type=content_type,
        defaults={"name": "Can use the Store Dashboard"},
    )
    group, _ = Group.objects.get_or_create(name=GROUP_NAME)
    group.permissions.add(permission)


def remove_store_manager_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_dashboard_access_permission"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            create_store_manager_group, remove_store_manager_group
        ),
    ]
