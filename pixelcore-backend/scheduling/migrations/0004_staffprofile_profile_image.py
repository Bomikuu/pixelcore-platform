from django.db import migrations, models

import scheduling.models


class Migration(migrations.Migration):
    dependencies = [("scheduling", "0003_booking_reminder_sent_at")]

    operations = [
        migrations.AddField(
            model_name="staffprofile",
            name="profile_image",
            field=models.ImageField(
                blank=True,
                null=True,
                max_length=500,
                upload_to=scheduling.models.staff_profile_image_path,
            ),
        ),
    ]
