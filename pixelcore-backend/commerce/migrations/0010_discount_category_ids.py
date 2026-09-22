from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("commerce", "0009_productrequestsettings_productrequest")]
    operations = [
        migrations.AddField(
            model_name="discount",
            name="category_ids",
            field=models.JSONField(default=list, blank=True),
        ),
    ]
