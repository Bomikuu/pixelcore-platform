from django.db import migrations, models


def include_primary_handlers(apps, schema_editor):
    VenueEvent = apps.get_model("scheduling", "VenueEvent")
    through_model = VenueEvent.assigned_staff.through
    through_model.objects.bulk_create(
        [
            through_model(venueevent_id=event.id, staffprofile_id=event.handler_id)
            for event in VenueEvent.objects.exclude(handler_id=None).iterator()
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0016_venueevent_handler_products"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="assigned_staff",
            field=models.ManyToManyField(
                blank=True,
                related_name="assigned_venue_events",
                to="scheduling.staffprofile",
            ),
        ),
        migrations.RunPython(include_primary_handlers, migrations.RunPython.noop),
    ]
