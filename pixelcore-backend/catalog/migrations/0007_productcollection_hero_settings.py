from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_remove_offeringmedia_unique_singleton_offering_media_role_and_more")]

    operations = [
        migrations.AddField(
            model_name="productcollection",
            name="hero_settings",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
