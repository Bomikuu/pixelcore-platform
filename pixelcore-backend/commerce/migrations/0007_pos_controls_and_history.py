from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("businesses", "0010_businessdevice_pairing_code_storage"), ("commerce", "0006_possession")]
    operations = [
        migrations.AddField(model_name="possession", name="held_sales", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="order", name="source_device", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="businesses.businessdevice")),
    ]
