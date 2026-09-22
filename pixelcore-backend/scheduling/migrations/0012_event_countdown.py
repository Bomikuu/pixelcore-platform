from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0011_event_template_popup_music"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="countdown_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="countdown_label",
            field=models.CharField(
                blank=True,
                default="Until we celebrate",
                max_length=80,
            ),
        ),
    ]
