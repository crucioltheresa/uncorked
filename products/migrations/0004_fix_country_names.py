from django.db import migrations


def fix_country_names(apps, schema_editor):
    """Fix country names in Region model for consistency."""
    Region = apps.get_model('products', 'Region')

    # Fix "Vin de France" -> "France"
    Region.objects.filter(country='Vin de France').update(country='France')

    # Fix "France (Vin de France)" -> "France"
    Region.objects.filter(country='France (Vin de France)').update(country='France')

    # Fix "Central Italy" -> "Italy"
    Region.objects.filter(country='Central Italy').update(country='Italy')

    # Fix "Slovenia (Vipava Valley)" -> "Slovenia"
    Region.objects.filter(country='Slovenia (Vipava Valley)').update(country='Slovenia')

    # Fix "South Australia" -> "Australia"
    Region.objects.filter(country='South Australia').update(country='Australia')


def reverse_fix(apps, schema_editor):
    """Reverse the country name fixes."""
    Region = apps.get_model('products', 'Region')

    # Revert France back to "Vin de France" where name is "Vin de France"
    Region.objects.filter(country='France', name='Vin de France').update(country='Vin de France')

    # Revert Italy back to "Central Italy"
    Region.objects.filter(country='Italy', name='Central Italy').update(country='Central Italy')

    # Revert Slovenia back to "Slovenia (Vipava Valley)"
    Region.objects.filter(country='Slovenia', name='Slovenia (Vipava Valley)').update(country='Slovenia (Vipava Valley)')

    # Revert Australia back to "South Australia"
    Region.objects.filter(country='Australia', name='Riverland').update(country='South Australia')


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_wine_slug'),
    ]

    operations = [
        migrations.RunPython(fix_country_names, reverse_fix),
    ]
