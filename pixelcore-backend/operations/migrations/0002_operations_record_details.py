import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventorybalance",
            name="bin_location",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="inventorybalance",
            name="last_counted_at",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="inventorybalance",
            name="notes",
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name="inventorybalance",
            name="reorder_quantity",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name="inventorybalance",
            name="target_stock_level",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name="inventorybalance",
            name="preferred_supplier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="preferred_inventory_balances",
                to="operations.supplier",
            ),
        ),
        migrations.AddField(
            model_name="supplier",
            name="account_reference",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="supplier",
            name="code",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="supplier",
            name="lead_time_days",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="supplier",
            name="payment_terms_days",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="supplier",
            name="website",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="ordered_at",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="shipping_address",
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="shipping_method",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="supplier_reference",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
