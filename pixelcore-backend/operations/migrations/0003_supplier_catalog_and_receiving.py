import django.db.models.deletion
import uuid
from django.db import migrations, models


def backfill_received_at(apps, schema_editor):
    PurchaseOrder = apps.get_model("operations", "PurchaseOrder")
    for purchase_order in PurchaseOrder.objects.filter(status="received", received_at__isnull=True).iterator():
        purchase_order.received_at = purchase_order.updated_at
        purchase_order.save(update_fields=["received_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("businesses", "0003_business_currency_locked_at_and_more"),
        ("catalog", "0001_initial"),
        ("operations", "0002_operations_record_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplier",
            name="category",
            field=models.CharField(
                choices=[
                    ("manufacturer", "Manufacturer"),
                    ("distributor", "Distributor"),
                    ("wholesaler", "Wholesaler"),
                    ("service_provider", "Service provider"),
                    ("contractor", "Contractor"),
                    ("marketplace", "Marketplace"),
                    ("other", "Other"),
                ],
                default="distributor",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="supplier",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="supplier_images",
                to="businesses.businessasset",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="received_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_received_at, migrations.RunPython.noop),
        migrations.CreateModel(
            name="SupplierProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("supplier_sku", models.CharField(blank=True, max_length=100)),
                ("supplier_product_name", models.CharField(blank=True, max_length=200)),
                ("last_unit_cost", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("minimum_order_quantity", models.DecimalField(decimal_places=3, default=1, max_digits=14)),
                ("lead_time_days", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="supplier_products", to="businesses.business")),
                ("supplier", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="supplied_products", to="operations.supplier")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="supplier_sources", to="catalog.offeringvariant")),
            ],
            options={
                "ordering": ["variant__offering__name", "variant__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="supplierproduct",
            constraint=models.UniqueConstraint(fields=("supplier", "variant"), name="unique_supplier_variant_source"),
        ),
    ]
