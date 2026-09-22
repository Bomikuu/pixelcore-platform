import django.core.validators
from django.db import migrations, models

import scheduling.models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0010_event_wedding_website"),
    ]

    operations = [
        migrations.AlterField(
            model_name="venueevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("wedding", "Wedding"),
                    ("birthday", "Birthday"),
                    ("general", "General event"),
                    ("private_event", "Private event"),
                    ("corporate", "Corporate event"),
                    ("community", "Community event"),
                    ("other", "Other event"),
                ],
                default="private_event",
                max_length=24,
            ),
        ),
        migrations.AlterField(
            model_name="venueevent",
            name="website_template",
            field=models.CharField(
                choices=[
                    ("wedding_editorial", "Editorial noir"),
                    ("wedding_garden", "Garden vow"),
                    ("wedding_modern", "Modern ceremony"),
                    ("birthday_color", "Color story"),
                    ("birthday_after_dark", "After dark"),
                    ("birthday_milestone", "Milestone portrait"),
                    ("general_spotlight", "Event spotlight"),
                    ("general_studio", "Studio programme"),
                    ("general_community", "Community canvas"),
                ],
                default="wedding_editorial",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="popup_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="popup_title",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="popup_message",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="popup_button_label",
            field=models.CharField(
                blank=True,
                default="Enter event",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="music_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="background_music",
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                upload_to=scheduling.models.venue_event_music_path,
            ),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="background_music_title",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="music_volume",
            field=models.PositiveSmallIntegerField(
                default=35,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
    ]
