import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0013_businesscard"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscard",
            name="background_apply_to",
            field=models.CharField(
                choices=[
                    ("front", "Front only"),
                    ("back", "Back only"),
                    ("both", "Both sides"),
                ],
                default="front",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_asset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="business_card_backgrounds",
                to="businesses.businessasset",
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_image_fit",
            field=models.CharField(
                choices=[("cover", "Cover"), ("contain", "Contain")],
                default="cover",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_image_position",
            field=models.CharField(
                choices=[
                    ("center", "Center"),
                    ("top", "Top"),
                    ("bottom", "Bottom"),
                    ("left", "Left"),
                    ("right", "Right"),
                ],
                default="center",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_overlay",
            field=models.CharField(
                choices=[
                    ("none", "None"),
                    ("light", "Light"),
                    ("dark", "Dark"),
                    ("brand", "Brand color"),
                ],
                default="dark",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_overlay_strength",
            field=models.CharField(
                choices=[
                    ("low", "Low"),
                    ("medium", "Medium"),
                    ("high", "High"),
                ],
                default="medium",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_type",
            field=models.CharField(
                choices=[
                    ("generated", "Generated pattern"),
                    ("image", "Image background"),
                ],
                default="generated",
                max_length=16,
            ),
        ),
    ]
