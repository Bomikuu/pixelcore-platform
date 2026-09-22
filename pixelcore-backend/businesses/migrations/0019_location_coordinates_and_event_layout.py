import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0018_businesscard_shared_design_controls"),
        ("scheduling", "0006_venue_layout_and_scheduling_settings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="businessevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("task", "Task"),
                    ("meeting", "Meeting"),
                    ("event", "Event or function"),
                    ("appointment", "Appointment"),
                    ("deadline", "Deadline"),
                    ("other", "Other"),
                ],
                default="task",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="businesslocation",
            name="latitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="businesslocation",
            name="longitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="businessevent",
            name="resource_layout",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="business_events",
                to="scheduling.resourcelayout",
            ),
        ),
    ]
