from django.db import migrations, models

import scheduling.models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0007_venueevent_eventguest"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="thumbnail",
            field=models.ImageField(
                blank=True,
                max_length=500,
                null=True,
                upload_to=scheduling.models.venue_event_thumbnail_path,
            ),
        ),
    ]
