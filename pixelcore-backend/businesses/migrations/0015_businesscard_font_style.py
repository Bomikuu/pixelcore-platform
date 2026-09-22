from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0014_businesscard_background"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscard",
            name="font_style",
            field=models.CharField(
                choices=[
                    ("modern", "Modern"),
                    ("editorial", "Editorial"),
                    ("geometric", "Geometric"),
                    ("warm", "Warm"),
                ],
                default="modern",
                max_length=16,
            ),
        ),
    ]
