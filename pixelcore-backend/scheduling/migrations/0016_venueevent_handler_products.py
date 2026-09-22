from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_productreview"),
        ("scheduling", "0015_event_wish_display_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="handler",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="handled_venue_events",
                to="scheduling.staffprofile",
            ),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="products",
            field=models.ManyToManyField(
                blank=True,
                related_name="venue_events",
                to="catalog.offering",
            ),
        ),
    ]
