from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("businesses", "0011_businessasset_processing_status_and_more")]

    operations = [
        migrations.AlterField(
            model_name="businessasset",
            name="asset_type",
            field=models.CharField(
                choices=[("image", "Image"), ("video", "Video"), ("document", "Document"), ("model", "3D model")],
                max_length=16,
            ),
        ),
    ]
