from django.db import migrations, models
import django.db.models.deletion


def classify_existing_resources(apps, schema_editor):
    Resource = apps.get_model("scheduling", "Resource")
    for resource in Resource.objects.select_related("resource_type").iterator():
        name = f"{resource.name} {resource.resource_type.name}".lower()
        resource.element_type = "table" if "table" in name else "other"
        resource.save(update_fields=["element_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0005_booking_confirmation_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="resourcelayout",
            name="description",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="resourcelayout",
            name="layout_type",
            field=models.CharField(
                choices=[
                    ("restaurant", "Restaurant dining"),
                    ("event", "Event or wedding"),
                    ("room", "Room or studio"),
                    ("general", "General venue"),
                ],
                default="general",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="element_type",
            field=models.CharField(
                choices=[
                    ("table", "Table or seating"),
                    ("stage", "Stage"),
                    ("dance_floor", "Dance floor"),
                    ("bar", "Bar"),
                    ("buffet", "Buffet or service station"),
                    ("entrance", "Entrance"),
                    ("booth", "Booth or exhibit"),
                    ("service", "Service area"),
                    ("decor", "Decor or landmark"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="height",
            field=models.PositiveSmallIntegerField(default=16),
        ),
        migrations.AddField(
            model_name="resource",
            name="is_bookable",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="resource",
            name="rotation",
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="resource",
            name="width",
            field=models.PositiveSmallIntegerField(default=16),
        ),
        migrations.RunPython(classify_existing_resources, migrations.RunPython.noop),
        migrations.CreateModel(
            name="SchedulingSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_booking_enabled", models.BooleanField(default=True)),
                ("public_intro", models.CharField(blank=True, max_length=280)),
                ("advance_booking_days", models.PositiveSmallIntegerField(default=31)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "business",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scheduling_settings",
                        to="businesses.business",
                    ),
                ),
            ],
        ),
    ]
