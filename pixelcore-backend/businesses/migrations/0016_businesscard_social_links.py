from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0015_businesscard_font_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscard",
            name="show_social_links",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="social_links",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
