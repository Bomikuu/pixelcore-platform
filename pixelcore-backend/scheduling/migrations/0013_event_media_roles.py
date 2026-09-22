from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0012_event_countdown"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventmedia",
            name="placement",
            field=models.CharField(
                choices=[
                    ("hero", "Hero"),
                    ("popup", "Popup"),
                    ("story", "Story"),
                    ("gallery", "Gallery"),
                    ("closing", "Closing"),
                ],
                default="gallery",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="eventstoryblock",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="story_blocks",
                to="scheduling.eventmedia",
            ),
        ),
    ]
