import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [("businesses", "0005_account_onboarding")]
    operations = [
        migrations.CreateModel(
            name="BusinessDevice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("device_type", models.CharField(choices=[("pos", "POS station"), ("customer_display", "Customer display"), ("attendance", "Attendance terminal"), ("signage", "Digital signage")], max_length=24)),
                ("pairing_code_digest", models.CharField(blank=True, db_index=True, max_length=64)),
                ("token_version", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("configuration", models.JSONField(blank=True, default=dict)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to="businesses.business")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_business_devices", to=settings.AUTH_USER_MODEL)),
                ("location", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devices", to="businesses.businesslocation")),
            ], options={"ordering": ["device_type", "name"]},
        ),
        migrations.AddConstraint(model_name="businessdevice", constraint=models.UniqueConstraint(fields=("business", "name"), name="unique_business_device_name")),
    ]
