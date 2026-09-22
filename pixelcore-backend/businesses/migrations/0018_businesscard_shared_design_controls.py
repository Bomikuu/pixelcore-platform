from django.db import migrations, models


FONT_CHOICES = [
    ("manrope", "Manrope"),
    ("newsreader", "Newsreader"),
    ("playfair", "Playfair Display"),
    ("cormorant", "Cormorant Garamond"),
    ("montserrat", "Montserrat"),
    ("jakarta", "Plus Jakarta Sans"),
    ("great_vibes", "Great Vibes"),
    ("allura", "Allura"),
    ("parisienne", "Parisienne"),
    ("alex_brush", "Alex Brush"),
    ("lobster", "Lobster"),
    ("playball", "Playball"),
    ("custom", "Custom uploaded font"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0017_businesscard_luxury_theme"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesscard",
            name="color_mode",
            field=models.CharField(
                choices=[("style", "Style default"), ("custom", "Custom")],
                default="style",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="typography_mode",
            field=models.CharField(
                choices=[("style", "Style default"), ("custom", "Custom")],
                default="style",
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="businesscard",
            name="heading_font",
            field=models.CharField(choices=FONT_CHOICES, default="cormorant", max_length=16),
        ),
        migrations.AlterField(
            model_name="businesscard",
            name="body_font",
            field=models.CharField(choices=FONT_CHOICES, default="manrope", max_length=16),
        ),
        migrations.AlterField(
            model_name="businesscard",
            name="accent_font",
            field=models.CharField(choices=FONT_CHOICES, default="great_vibes", max_length=16),
        ),
    ]
