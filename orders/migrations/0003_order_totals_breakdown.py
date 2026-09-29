from decimal import Decimal

from django.db import migrations, models
from django.db.models import F


def backfill_subtotal(apps, schema_editor):
    """Existing orders had no discount or delivery: subtotal = old total."""
    Order = apps.get_model("orders", "Order")
    Order.objects.update(subtotal=F("grand_total"))


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_order_number_alter_order_id_alter_orderitem_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="total_price",
            new_name="grand_total",
        ),
        migrations.AddField(
            model_name="order",
            name="subtotal",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=10
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="discount",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=10
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_cost",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=10
            ),
        ),
        migrations.RunPython(backfill_subtotal, migrations.RunPython.noop),
    ]
