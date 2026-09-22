from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("businesses", "0009_expand_order_station_device_types")]
    operations = [
        migrations.AddField(model_name="businessdevice", name="pairing_code_encrypted", field=models.TextField(blank=True)),
        migrations.AddField(model_name="businessdevice", name="pairing_code_issued_at", field=models.DateTimeField(blank=True, null=True)),
    ]
