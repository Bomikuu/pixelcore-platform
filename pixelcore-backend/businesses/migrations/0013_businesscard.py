import django.core.validators
import django.db.models.deletion
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0012_alter_businessasset_asset_type"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BusinessCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("display_name", models.CharField(max_length=160)),
                ("job_title", models.CharField(blank=True, max_length=120)),
                ("headline", models.CharField(blank=True, max_length=220)),
                ("email", models.EmailField(blank=True, max_length=254)),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[0-9+().\\-\\s]*$",
                                "Enter a valid phone number.",
                            )
                        ],
                    ),
                ),
                (
                    "style",
                    models.CharField(
                        choices=[
                            ("signature", "Signature"),
                            ("editorial", "Editorial"),
                            ("studio", "Studio"),
                        ],
                        default="signature",
                        max_length=16,
                    ),
                ),
                (
                    "orientation",
                    models.CharField(
                        choices=[("landscape", "Landscape"), ("portrait", "Portrait")],
                        default="landscape",
                        max_length=16,
                    ),
                ),
                ("show_email", models.BooleanField(default=True)),
                ("show_phone", models.BooleanField(default=True)),
                ("show_business_address", models.BooleanField(default=True)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="business_cards",
                        to="businesses.business",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="business_cards",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["business_id", "user_id"]},
        ),
        migrations.AddConstraint(
            model_name="businesscard",
            constraint=models.UniqueConstraint(
                fields=("business", "user"),
                name="unique_member_business_card",
            ),
        ),
    ]
