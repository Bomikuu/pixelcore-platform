import django.core.validators
import django.db.models.deletion
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
    ("custom", "Custom uploaded font"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0016_businesscard_social_links"),
    ]

    operations = [
        migrations.AlterField(
            model_name="businessasset",
            name="asset_type",
            field=models.CharField(
                choices=[
                    ("image", "Image"),
                    ("video", "Video"),
                    ("document", "Document"),
                    ("model", "3D model"),
                    ("font", "Font"),
                ],
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="businesscard",
            name="style",
            field=models.CharField(
                choices=[
                    ("signature", "Signature"),
                    ("editorial", "Editorial"),
                    ("studio", "Studio"),
                    ("luxury", "Luxury"),
                ],
                default="signature",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="heading_font",
            field=models.CharField(choices=FONT_CHOICES, default="cormorant", max_length=16),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="body_font",
            field=models.CharField(choices=FONT_CHOICES, default="manrope", max_length=16),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="accent_font",
            field=models.CharField(choices=FONT_CHOICES, default="great_vibes", max_length=16),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="custom_font_asset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="business_card_fonts",
                to="businesses.businessasset",
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="background_color",
            field=models.CharField(
                default="#0B0B0D",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#[0-9A-Fa-f]{6}$",
                        "Enter a six-digit hex color.",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="text_color",
            field=models.CharField(
                default="#F8F1E1",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#[0-9A-Fa-f]{6}$",
                        "Enter a six-digit hex color.",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="accent_color",
            field=models.CharField(
                default="#C8A96B",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#[0-9A-Fa-f]{6}$",
                        "Enter a six-digit hex color.",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="border_color",
            field=models.CharField(
                default="#BFA36A",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#[0-9A-Fa-f]{6}$",
                        "Enter a six-digit hex color.",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="ornament_color",
            field=models.CharField(
                default="#C8A96B",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        "^#[0-9A-Fa-f]{6}$",
                        "Enter a six-digit hex color.",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="businesscard",
            name="show_qr",
            field=models.BooleanField(default=True),
        ),
    ]
