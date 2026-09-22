import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("businesses", "0006_business_device"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("link_type", models.CharField(choices=[("customer_display", "Customer display")], default="customer_display", max_length=24)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="device_links", to="businesses.business")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_device_links", to=settings.AUTH_USER_MODEL)),
                ("source_device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_links", to="businesses.businessdevice")),
                ("target_device", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_link", to="businesses.businessdevice")),
            ],
            options={"ordering": ["target_device__name", "id"]},
        ),
        migrations.AddConstraint(
            model_name="devicelink",
            constraint=models.UniqueConstraint(fields=("source_device", "target_device"), name="unique_device_link_pair"),
        ),
    ]
