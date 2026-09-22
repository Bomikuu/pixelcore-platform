import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import uuid
import workforce.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("businesses", "0006_business_device"), ("scheduling", "0002_resources_and_staff_operations"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="StaffDocument", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("document_type", models.CharField(choices=[("identity", "Identity"), ("contract", "Employment contract"), ("certification", "Certification"), ("permit", "Permit"), ("food_safety", "Food safety"), ("other", "Other")], max_length=24)),
            ("file", models.FileField(upload_to=workforce.models.staff_document_path)), ("original_name", models.CharField(max_length=255)),
            ("status", models.CharField(choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=16)),
            ("review_notes", models.TextField(blank=True, max_length=2000)), ("reviewed_at", models.DateTimeField(blank=True, null=True)), ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="staff_documents", to="businesses.business")),
            ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_staff_documents", to=settings.AUTH_USER_MODEL)),
            ("staff", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="scheduling.staffprofile")),
        ], options={"ordering": ["-uploaded_at", "-id"]}),
        migrations.CreateModel(name="AttendanceRecord", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("clock_in", models.DateTimeField(blank=True, null=True)), ("clock_out", models.DateTimeField(blank=True, null=True)), ("scheduled_start", models.DateTimeField(blank=True, null=True)),
            ("late_minutes", models.PositiveSmallIntegerField(default=0)), ("late_reason", models.TextField(blank=True, max_length=1000)), ("late_excused", models.BooleanField(default=False)),
            ("override_reason", models.TextField(blank=True, max_length=1000)), ("overridden_at", models.DateTimeField(blank=True, null=True)),
            ("status", models.CharField(choices=[("present", "Present"), ("late", "Late"), ("leave", "On leave"), ("absent", "Absent")], default="present", max_length=12)),
            ("notes", models.TextField(blank=True, max_length=2000)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="businesses.business")),
            ("location", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attendance_records", to="businesses.businesslocation")),
            ("overridden_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attendance_overrides", to=settings.AUTH_USER_MODEL)),
            ("staff", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="scheduling.staffprofile")),
        ], options={"ordering": ["-clock_in", "-created_at"]}),
        migrations.AddConstraint(model_name="attendancerecord", constraint=models.UniqueConstraint(condition=models.Q(clock_in__isnull=False, clock_out__isnull=True), fields=("staff",), name="unique_active_staff_attendance")),
        migrations.CreateModel(name="LeaveRequest", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("leave_type", models.CharField(choices=[("vacation", "Vacation"), ("sick", "Sick leave"), ("personal", "Personal leave"), ("emergency", "Emergency leave"), ("unpaid", "Unpaid leave")], default="vacation", max_length=16)),
            ("start_date", models.DateField()), ("end_date", models.DateField()), ("partial_day", models.BooleanField(default=False)), ("reason", models.TextField(max_length=2000)),
            ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled")], default="pending", max_length=12)),
            ("review_notes", models.TextField(blank=True, max_length=2000)), ("reviewed_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="leave_requests", to="businesses.business")),
            ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_leave_requests", to=settings.AUTH_USER_MODEL)),
            ("staff", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="leave_requests", to="scheduling.staffprofile")),
        ], options={"ordering": ["-created_at", "-id"]}),
        migrations.CreateModel(name="AttendanceFlag", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("flag_type", models.CharField(default="consecutive_late", max_length=24)), ("status", models.CharField(choices=[("open", "Open"), ("overridden", "Overridden"), ("resolved", "Resolved")], default="open", max_length=16)),
            ("occurrence_count", models.PositiveSmallIntegerField(default=0)), ("first_occurrence", models.DateField()), ("last_occurrence", models.DateField()), ("summary", models.CharField(max_length=255)),
            ("override_reason", models.TextField(blank=True, max_length=1000)), ("reviewed_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_flags", to="businesses.business")),
            ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_attendance_flags", to=settings.AUTH_USER_MODEL)),
            ("staff", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_flags", to="scheduling.staffprofile")),
        ], options={"ordering": ["-created_at", "-id"]}),
        migrations.AddConstraint(model_name="attendanceflag", constraint=models.UniqueConstraint(condition=models.Q(("status", "open")), fields=("staff", "flag_type"), name="unique_open_staff_attendance_flag")),
    ]
