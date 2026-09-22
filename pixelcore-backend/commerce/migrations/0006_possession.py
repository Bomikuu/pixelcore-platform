import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0007_devicelink"),
        ("commerce", "0005_cartitem_selection_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="PosSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("cart_snapshot", models.JSONField(blank=True, default=dict)),
                ("revision", models.PositiveBigIntegerField(default=0)),
                ("last_checkout_key", models.CharField(blank=True, max_length=120)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pos_sessions", to="businesses.business")),
                ("last_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pos_sessions", to="commerce.order")),
                ("station", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="pos_session", to="businesses.businessdevice")),
            ],
            options={"ordering": ["-updated_at", "id"]},
        ),
    ]
