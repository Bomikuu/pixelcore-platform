from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0014_event_participant_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="wish_display_mode",
            field=models.CharField(
                choices=[
                    ("realtime", "Show as approved"),
                    ("event_day", "Reveal on event day"),
                ],
                default="realtime",
                max_length=16,
            ),
        ),
    ]
