import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [("businesses", "0005_account_onboarding"), ("catalog", "0002_remove_offeringvariant_unique_offering_variant_sku_and_more")]
    operations = [
        migrations.CreateModel(name="OptionGroup", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("name", models.CharField(max_length=120)), ("minimum_choices", models.PositiveSmallIntegerField(default=0)), ("maximum_choices", models.PositiveSmallIntegerField(default=1)), ("is_required", models.BooleanField(default=False)), ("sort_order", models.PositiveIntegerField(default=0)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="option_groups", to="businesses.business")), ("offering", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="option_groups", to="catalog.offering")),
        ], options={"ordering": ["sort_order", "name"]}),
        migrations.AddConstraint(model_name="optiongroup", constraint=models.UniqueConstraint(fields=("offering", "name"), name="unique_offering_option_group")),
        migrations.CreateModel(name="OfferingOption", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("name", models.CharField(max_length=120)), ("price_delta", models.DecimalField(decimal_places=2, default=0, max_digits=12)), ("cost_delta", models.DecimalField(decimal_places=2, default=0, max_digits=12)), ("is_active", models.BooleanField(default=True)), ("sort_order", models.PositiveIntegerField(default=0)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offering_options", to="businesses.business")), ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="catalog.optiongroup")),
        ], options={"ordering": ["sort_order", "name"]}),
        migrations.AddConstraint(model_name="offeringoption", constraint=models.UniqueConstraint(fields=("group", "name"), name="unique_group_offering_option")),
        migrations.CreateModel(name="OfferingFoodProfile", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ("serving_label", models.CharField(blank=True, max_length=100)),
            ("calories", models.PositiveIntegerField(blank=True, null=True)), ("protein_grams", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)), ("carbohydrate_grams", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)), ("fat_grams", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
            ("allergens", models.JSONField(blank=True, default=list)), ("ingredients", models.TextField(blank=True, max_length=4000)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="food_profiles", to="businesses.business")), ("offering", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="food_profile", to="catalog.offering")),
        ]),
        migrations.CreateModel(name="OfferingCostComponent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("name", models.CharField(max_length=160)), ("quantity", models.DecimalField(decimal_places=3, default=1, max_digits=12)), ("unit", models.CharField(default="unit", max_length=40)), ("unit_cost", models.DecimalField(decimal_places=2, max_digits=12)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offering_cost_components", to="businesses.business")), ("offering", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cost_components", to="catalog.offering")),
        ], options={"ordering": ["name"]}),
    ]
