from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0003_options_food_and_costing"),
        ("commerce", "0003_alter_orderitem_offering"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="business_customer_profiles", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="Discount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("code", models.CharField(blank=True, max_length=40)),
                ("value_type", models.CharField(choices=[("percentage", "Percentage"), ("fixed", "Fixed amount")], max_length=16)),
                ("value", models.DecimalField(decimal_places=2, max_digits=12)),
                ("is_automatic", models.BooleanField(default=False)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("offering_ids", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="discounts", to="businesses.business")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="SavedOffering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_offerings", to="businesses.business")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_offerings", to="commerce.customer")),
                ("offering", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_by_customers", to="catalog.offering")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="discount",
            constraint=models.UniqueConstraint(condition=models.Q(("code", ""), _negated=True), fields=("business", "code"), name="unique_business_discount_code"),
        ),
        migrations.AddConstraint(
            model_name="savedoffering",
            constraint=models.UniqueConstraint(fields=("customer", "offering"), name="unique_customer_saved_offering"),
        ),
    ]
