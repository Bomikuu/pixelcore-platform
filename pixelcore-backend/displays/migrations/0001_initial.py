import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [("businesses", "0006_business_device"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="DisplayPublication", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("name", models.CharField(max_length=120)), ("kind", models.CharField(choices=[("catalog_board", "Catalog board"), ("promotion", "Promotional poster"), ("information", "Information screen"), ("qr_catalog", "QR catalog")], max_length=24)),
            ("template", models.CharField(choices=[("poster_menu", "Poster Menu"), ("feature_rows", "Feature rows"), ("triple_grid", "Triple grid"), ("hero_list", "Hero and list"), ("freeform", "Freeform canvas"), ("mobile_catalog", "Mobile catalog")], default="feature_rows", max_length=24)),
            ("schema_version", models.PositiveSmallIntegerField(default=1)), ("settings", models.JSONField(blank=True, default=dict)), ("offering_ids", models.JSONField(blank=True, default=list)),
            ("share_key", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ("is_active", models.BooleanField(default=True)), ("is_published", models.BooleanField(default=False)),
            ("published_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("background_asset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="display_backgrounds", to="businesses.businessasset")),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="display_publications", to="businesses.business")),
            ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_display_publications", to=settings.AUTH_USER_MODEL)),
            ("location", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="display_publications", to="businesses.businesslocation")),
        ], options={"ordering": ["kind", "name"]}),
        migrations.AddConstraint(model_name="displaypublication", constraint=models.UniqueConstraint(fields=("business", "name"), name="unique_business_display_name")),
        migrations.CreateModel(name="DisplayDeviceAssignment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("assigned_at", models.DateTimeField(auto_now_add=True)),
            ("device", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="display_assignment", to="businesses.businessdevice")),
            ("publication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="device_assignments", to="displays.displaypublication")),
        ]),
        migrations.AddConstraint(model_name="displaydeviceassignment", constraint=models.UniqueConstraint(fields=("publication", "device"), name="unique_publication_device")),
    ]
