from django.utils import timezone
from rest_framework import serializers

from businesses.models import BusinessLocation
from scheduling.models import StaffProfile
from .models import AttendanceFlag, AttendanceRecord, LeaveRequest, StaffDocument


class StaffRelationMixin:
    staff_public_id = serializers.SlugRelatedField(source="staff", slug_field="public_id", queryset=StaffProfile.objects.all())

    def validate_staff_public_id(self, staff):
        if staff.business_id != self.context["business"].id:
            raise serializers.ValidationError("Choose staff from this business.")
        return staff


class StaffDocumentSerializer(StaffRelationMixin, serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(
        source="staff",
        slug_field="public_id",
        queryset=StaffProfile.objects.all(),
    )
    file_url = serializers.SerializerMethodField()
    class Meta:
        model = StaffDocument
        fields = ["public_id", "staff_public_id", "document_type", "file", "file_url", "original_name", "status", "review_notes", "reviewed_at", "uploaded_at"]
        read_only_fields = ["public_id", "file_url", "original_name", "status", "reviewed_at", "uploaded_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def validate_file(self, upload):
        allowed = {"application/pdf", "image/jpeg", "image/png"}
        if getattr(upload, "content_type", "") not in allowed or upload.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Use a PDF, JPG, or PNG file up to 10 MB.")
        return upload

    def create(self, validated_data):
        upload = validated_data["file"]
        validated_data.pop("business", None)
        return StaffDocument.objects.create(business=self.context["business"], original_name=upload.name[:255], **validated_data)

    def get_file_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class AttendanceRecordSerializer(StaffRelationMixin, serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(
        source="staff",
        slug_field="public_id",
        queryset=StaffProfile.objects.all(),
    )
    staff_name = serializers.CharField(source="staff.display_name", read_only=True)
    worked_minutes = serializers.SerializerMethodField()
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all(), required=False, allow_null=True)
    class Meta:
        model = AttendanceRecord
        fields = ["public_id", "staff_public_id", "staff_name", "location_public_id", "clock_in", "clock_out", "scheduled_start", "worked_minutes", "late_minutes", "late_reason", "late_excused", "override_reason", "status", "notes", "created_at", "updated_at"]
        read_only_fields = ["public_id", "staff_name", "worked_minutes", "created_at", "updated_at"]

    def validate_location_public_id(self, location):
        if location.business_id != self.context["business"].id:
            raise serializers.ValidationError("Choose a location from this business.")
        return location

    def get_worked_minutes(self, obj):
        if not obj.clock_in:
            return 0
        boundary = obj.clock_out or timezone.now()
        return max(0, int((boundary - obj.clock_in).total_seconds() // 60))


class LeaveRequestSerializer(StaffRelationMixin, serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(
        source="staff",
        slug_field="public_id",
        queryset=StaffProfile.objects.all(),
    )
    staff_name = serializers.CharField(source="staff.display_name", read_only=True)
    class Meta:
        model = LeaveRequest
        fields = ["public_id", "staff_public_id", "staff_name", "leave_type", "start_date", "end_date", "partial_day", "reason", "status", "review_notes", "reviewed_at", "created_at", "updated_at"]
        read_only_fields = ["public_id", "staff_name", "reviewed_at", "created_at", "updated_at"]
    def validate(self, attrs):
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date must be on or after start date."})
        return attrs


class AttendanceFlagSerializer(StaffRelationMixin, serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(
        source="staff",
        slug_field="public_id",
        queryset=StaffProfile.objects.all(),
    )
    staff_name = serializers.CharField(source="staff.display_name", read_only=True)
    class Meta:
        model = AttendanceFlag
        fields = ["public_id", "staff_public_id", "staff_name", "flag_type", "status", "occurrence_count", "first_occurrence", "last_occurrence", "summary", "override_reason", "reviewed_at", "created_at"]
        read_only_fields = ["public_id", "staff_public_id", "staff_name", "flag_type", "occurrence_count", "first_occurrence", "last_occurrence", "summary", "created_at"]

    def update(self, instance, validated_data):
        if "status" in validated_data or "override_reason" in validated_data:
            instance.reviewed_by = self.context["request"].user
            instance.reviewed_at = timezone.now()
        return super().update(instance, validated_data)
