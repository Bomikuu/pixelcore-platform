import django.db.models.deletion
from django.db import migrations, models
import scheduling.models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0005_account_onboarding"),
        ("scheduling", "0001_initial"),
    ]

    operations = [
        migrations.AddField(model_name="staffprofile", name="employee_code", field=models.CharField(default=scheduling.models.staff_code, editable=False, max_length=16, unique=True)),
        migrations.AddField(model_name="staffprofile", name="job_title", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="staffprofile", name="employment_status", field=models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("suspended", "Suspended"), ("inactive", "Inactive")], default="active", max_length=16)),
        migrations.AddField(model_name="staffprofile", name="hired_at", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="staffprofile", name="emergency_contact_name", field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name="staffprofile", name="emergency_contact_phone", field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(model_name="staffprofile", name="scheduled_start_time", field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name="staffprofile", name="scheduled_end_time", field=models.TimeField(blank=True, null=True)),
        migrations.AddField(model_name="staffprofile", name="late_grace_minutes", field=models.PositiveSmallIntegerField(default=10)),
        migrations.AddField(model_name="staffprofile", name="consecutive_late_threshold", field=models.PositiveSmallIntegerField(default=3)),
        migrations.AddField(model_name="staffprofile", name="attendance_pin_digest", field=models.CharField(blank=True, db_index=True, max_length=64)),
        migrations.AddField(model_name="staffprofile", name="attendance_pin_generated_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(
            name="ResourceType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=100)), ("singular_label", models.CharField(max_length=80)), ("plural_label", models.CharField(max_length=80)),
                ("icon", models.CharField(default="layout-grid", max_length=40)), ("is_active", models.BooleanField(default=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resource_types", to="businesses.business")),
            ], options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(model_name="resourcetype", constraint=models.UniqueConstraint(fields=("business", "name"), name="unique_business_resource_type")),
        migrations.CreateModel(
            name="ResourceLayout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ("name", models.CharField(max_length=120)),
                ("width", models.PositiveSmallIntegerField(default=100)), ("height", models.PositiveSmallIntegerField(default=100)), ("is_active", models.BooleanField(default=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resource_layouts", to="businesses.business")),
                ("location", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resource_layouts", to="businesses.businesslocation")),
            ], options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(model_name="resourcelayout", constraint=models.UniqueConstraint(fields=("location", "name"), name="unique_location_resource_layout")),
        migrations.CreateModel(
            name="Resource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=100)), ("capacity", models.PositiveSmallIntegerField(default=1)),
                ("shape", models.CharField(choices=[("round", "Round"), ("square", "Square"), ("rectangle", "Rectangle")], default="square", max_length=16)),
                ("position_x", models.PositiveSmallIntegerField(default=20)), ("position_y", models.PositiveSmallIntegerField(default=20)), ("is_active", models.BooleanField(default=True)), ("metadata", models.JSONField(blank=True, default=dict)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="businesses.business")),
                ("layout", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resources", to="scheduling.resourcelayout")),
                ("location", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resources", to="businesses.businesslocation")),
                ("resource_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resources", to="scheduling.resourcetype")),
            ], options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(model_name="resource", constraint=models.UniqueConstraint(fields=("location", "name"), name="unique_location_resource_name")),
        migrations.CreateModel(
            name="BookingResource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("quantity", models.PositiveSmallIntegerField(default=1)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resource_allocations", to="scheduling.booking")),
                ("resource", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="booking_allocations", to="scheduling.resource")),
            ],
        ),
        migrations.AddField(model_name="booking", name="resources", field=models.ManyToManyField(blank=True, related_name="bookings", through="scheduling.BookingResource", to="scheduling.resource")),
        migrations.AddConstraint(model_name="bookingresource", constraint=models.UniqueConstraint(fields=("booking", "resource"), name="unique_booking_resource")),
    ]
