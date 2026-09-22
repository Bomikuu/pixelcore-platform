from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("businesses", "0008_alter_businessasset_file")]

    operations = [
        migrations.AlterField(
            model_name="businessdevice",
            name="device_type",
            field=models.CharField(
                choices=[
                    ("pos", "POS station"),
                    ("customer_display", "Customer display"),
                    ("kitchen_display", "Fulfillment display"),
                    ("dispatch_display", "Delivery display"),
                    ("attendance", "Attendance terminal"),
                    ("signage", "Digital signage"),
                ],
                max_length=24,
            ),
        ),
    ]
