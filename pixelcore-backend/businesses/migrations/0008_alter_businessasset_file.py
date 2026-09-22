from django.db import migrations, models

import businesses.models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0007_devicelink"),
    ]

    operations = [
        migrations.AlterField(
            model_name="businessasset",
            name="file",
            field=models.FileField(max_length=500, upload_to=businesses.models.library_asset_path),
        ),
    ]
