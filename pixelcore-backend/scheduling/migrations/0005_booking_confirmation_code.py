from django.db import migrations, models
import scheduling.models


def populate_confirmation_codes(apps, schema_editor):
    Booking = apps.get_model("scheduling", "Booking")
    for booking in Booking.objects.filter(confirmation_code="").iterator():
        code = scheduling.models.booking_confirmation_code()
        while Booking.objects.filter(confirmation_code=code).exists():
            code = scheduling.models.booking_confirmation_code()
        booking.confirmation_code = code
        booking.save(update_fields=["confirmation_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0004_staffprofile_profile_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="confirmation_code",
            field=models.CharField(default="", max_length=16),
        ),
        migrations.RunPython(
            populate_confirmation_codes,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="booking",
            name="confirmation_code",
            field=models.CharField(
                default=scheduling.models.booking_confirmation_code,
                editable=False,
                max_length=16,
                unique=True,
            ),
        ),
    ]
