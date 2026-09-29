from django.conf import settings
from django.db import migrations

SITE_NAME = "Uncorked"
SITE_DOMAIN = "uncorked-store-5dff5e1aa357.herokuapp.com"


def set_site(apps, schema_editor):
    """Replace the default "example.com" site with the Uncorked site."""
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={"name": SITE_NAME, "domain": SITE_DOMAIN},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_add_email_address_records"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(set_site, migrations.RunPython.noop),
    ]
