import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from businesses.models import Business, BusinessLocation
from scheduling.models import StaffProfile


def attendance_action_code_expiry():
    return timezone.now() + timedelta(minutes=5)


def staff_document_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    return f"businesses/{instance.business.public_id}/workforce/{instance.staff.public_id}/{uuid.uuid4().hex}{extension}"


class StaffDocument(models.Model):
    TYPE_CHOICES = [("identity", "Identity"), ("contract", "Employment contract"), ("certification", "Certification"), ("permit", "Permit"), ("food_safety", "Food safety"), ("other", "Other")]
    STATUS_CHOICES = [("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="staff_documents")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    file = models.FileField(upload_to=staff_document_path)
    original_name = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    review_notes = models.TextField(blank=True, max_length=2000)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_staff_documents")
    reviewed_at = models.DateTimeField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [("present", "Present"), ("late", "Late"), ("leave", "On leave"), ("absent", "Absent")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="attendance_records")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="attendance_records")
    location = models.ForeignKey(BusinessLocation, on_delete=models.SET_NULL, blank=True, null=True, related_name="attendance_records")
    clock_in = models.DateTimeField(blank=True, null=True)
    clock_out = models.DateTimeField(blank=True, null=True)
    scheduled_start = models.DateTimeField(blank=True, null=True)
    late_minutes = models.PositiveSmallIntegerField(default=0)
    late_reason = models.TextField(blank=True, max_length=1000)
    late_excused = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True, max_length=1000)
    overridden_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="attendance_overrides")
    overridden_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="present")
    notes = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-clock_in", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["staff"], condition=models.Q(clock_in__isnull=False, clock_out__isnull=True), name="unique_active_staff_attendance")]


class AttendanceActionCode(models.Model):
    ACTION_CHOICES = [
        ("clock_in", "Clock in"),
        ("clock_out", "Clock out"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="attendance_action_codes",
    )
    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="attendance_action_codes",
    )
    action = models.CharField(max_length=12, choices=ACTION_CHOICES)
    code_digest = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField(default=attendance_action_code_expiry)
    consumed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["business", "code_digest", "expires_at"],
                name="workforce_action_code_lookup",
            )
        ]


class LeaveRequest(models.Model):
    TYPE_CHOICES = [("vacation", "Vacation"), ("sick", "Sick leave"), ("personal", "Personal leave"), ("emergency", "Emergency leave"), ("unpaid", "Unpaid leave")]
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="leave_requests")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="vacation")
    start_date = models.DateField()
    end_date = models.DateField()
    partial_day = models.BooleanField(default=False)
    reason = models.TextField(max_length=2000)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    review_notes = models.TextField(blank=True, max_length=2000)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_leave_requests")
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class AttendanceFlag(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("overridden", "Overridden"), ("resolved", "Resolved")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="attendance_flags")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="attendance_flags")
    flag_type = models.CharField(max_length=24, default="consecutive_late")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    occurrence_count = models.PositiveSmallIntegerField(default=0)
    first_occurrence = models.DateField()
    last_occurrence = models.DateField()
    summary = models.CharField(max_length=255)
    override_reason = models.TextField(blank=True, max_length=1000)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_attendance_flags")
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["staff", "flag_type"], condition=models.Q(status="open"), name="unique_open_staff_attendance_flag")]
