from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0013_event_media_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="header_mark_text",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="header_mark_type",
            field=models.CharField(
                choices=[("text", "Text"), ("logo", "Business logo")],
                default="text",
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="eventmedia",
            name="placement",
            field=models.CharField(
                choices=[
                    ("hero", "Hero"),
                    ("popup", "Popup"),
                    ("participant", "Participant"),
                    ("story", "Story"),
                    ("gallery", "Gallery"),
                    ("closing", "Closing"),
                ],
                default="gallery",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="eventparticipant",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="participants",
                to="scheduling.eventmedia",
            ),
        ),
    ]
