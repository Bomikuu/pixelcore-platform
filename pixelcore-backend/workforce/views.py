from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.api import BusinessScopedModelViewSet
from businesses.services import device_from_token, record_audit
from businesses.views import member_business
from scheduling.models import StaffProfile
from .models import AttendanceFlag, AttendanceRecord, LeaveRequest, StaffDocument
from .serializers import AttendanceFlagSerializer, AttendanceRecordSerializer, LeaveRequestSerializer, StaffDocumentSerializer
from .services import (
    consume_attendance_action_code,
    issue_attendance_action_code,
    issue_staff_pin,
)


class StaffDocumentViewSet(BusinessScopedModelViewSet):
    queryset = StaffDocument.objects.select_related("staff", "reviewed_by")
    serializer_class = StaffDocumentSerializer
    audit_resource = "staff_document"

    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get("staff_public_id")
        return queryset.filter(staff__public_id=staff_id) if staff_id else queryset

    @action(detail=True, methods=["post"])
    def review(self, request, business_public_id=None, public_id=None):
        document = self.get_object()
        decision = request.data.get("status")
        if decision not in {"approved", "rejected"}:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose approved or rejected.", "details": {}}}, status=400)
        document.status = decision
        document.review_notes = str(request.data.get("review_notes", ""))[:2000]
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.save(update_fields=["status", "review_notes", "reviewed_by", "reviewed_at"])
        record_audit(document.business, request.user, f"staff_document.{decision}", "staff_document", document.public_id)
        return Response(self.get_serializer(document).data)


class AttendanceRecordViewSet(BusinessScopedModelViewSet):
    queryset = AttendanceRecord.objects.select_related("staff", "location")
    serializer_class = AttendanceRecordSerializer
    http_method_names = ["get", "patch", "head", "options"]
    audit_resource = "attendance_record"

    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get("staff_public_id")
        return queryset.filter(staff__public_id=staff_id) if staff_id else queryset

    def perform_update(self, serializer):
        instance = serializer.save(overridden_by=self.request.user, overridden_at=timezone.now())
        record_audit(instance.business, self.request.user, "attendance.reviewed", "attendance_record", instance.public_id)


class LeaveRequestViewSet(BusinessScopedModelViewSet):
    queryset = LeaveRequest.objects.select_related("staff", "reviewed_by")
    serializer_class = LeaveRequestSerializer
    audit_resource = "leave_request"

    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get("staff_public_id")
        return queryset.filter(staff__public_id=staff_id) if staff_id else queryset

    def perform_update(self, serializer):
        instance = serializer.save(reviewed_by=self.request.user, reviewed_at=timezone.now())
        record_audit(instance.business, self.request.user, "leave_request.reviewed", "leave_request", instance.public_id, {"status": instance.status})


class AttendanceFlagViewSet(BusinessScopedModelViewSet):
    queryset = AttendanceFlag.objects.select_related("staff", "reviewed_by")
    serializer_class = AttendanceFlagSerializer
    http_method_names = ["get", "patch", "head", "options"]
    audit_resource = "attendance_flag"

    def get_queryset(self):
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get("staff_public_id")
        return queryset.filter(staff__public_id=staff_id) if staff_id else queryset


def employee_profile_for_user(user, business):
    return get_object_or_404(
        StaffProfile.objects.select_related("membership", "business"),
        business=business,
        membership__user=user,
        membership__status="active",
        is_active=True,
    )


def leave_days(request):
    days = (request.end_date - request.start_date).days + 1
    return 0.5 if request.partial_day else float(days)


def employee_summary_payload(staff, request):
    now = timezone.now()
    period_start = now - timedelta(days=30)
    attendance_queryset = staff.attendance_records.select_related("location").order_by(
        "-clock_in", "-created_at"
    )
    recent_attendance = list(
        attendance_queryset.filter(
            Q(clock_in__gte=period_start)
            | Q(clock_in__isnull=True, created_at__gte=period_start)
        )
    )
    leave_queryset = staff.leave_requests.order_by("-created_at")
    current_year_leave = list(
        leave_queryset.filter(status="approved", start_date__year=now.year)
    )
    document_queryset = staff.documents.order_by("-uploaded_at")
    flag_queryset = staff.attendance_flags.order_by("-created_at")
    attendance = list(attendance_queryset[:24])
    leave_requests = list(leave_queryset[:24])
    documents = list(document_queryset[:24])
    flags = list(flag_queryset[:12])
    worked_minutes = sum(
        max(
            0,
            int(((record.clock_out or now) - record.clock_in).total_seconds() // 60),
        )
        for record in recent_attendance
        if record.clock_in
    )
    summary = {
        "is_clocked_in": attendance_queryset.filter(
            clock_in__isnull=False,
            clock_out__isnull=True,
        ).exists(),
        "worked_minutes_30d": worked_minutes,
        "shifts_30d": len(recent_attendance),
        "late_shifts_30d": sum(1 for item in recent_attendance if item.late_minutes > 0),
        "approved_leave_days": sum(leave_days(item) for item in current_year_leave),
        "vacation_days": sum(
            leave_days(item) for item in current_year_leave if item.leave_type == "vacation"
        ),
        "sick_days": sum(
            leave_days(item) for item in current_year_leave if item.leave_type == "sick"
        ),
        "pending_leave_requests": leave_queryset.filter(status="pending").count(),
        "approved_documents": document_queryset.filter(status="approved").count(),
        "document_count": document_queryset.count(),
        "open_attendance_flags": flag_queryset.filter(status="open").count(),
    }
    context = {"request": request, "business": staff.business}
    from scheduling.serializers import StaffProfileSerializer

    return {
        "employee": StaffProfileSerializer(staff, context=context).data,
        "summary": summary,
        "attendance": AttendanceRecordSerializer(attendance, many=True, context=context).data,
        "leave_requests": LeaveRequestSerializer(leave_requests, many=True, context=context).data,
        "documents": StaffDocumentSerializer(documents, many=True, context=context).data,
        "attendance_flags": AttendanceFlagSerializer(flags, many=True, context=context).data,
    }


class EmployeePortalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        staff = employee_profile_for_user(request.user, business)
        return Response(employee_summary_payload(staff, request))


class EmployeeAttendancePinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        return Response(
            {
                "error": {
                    "code": "ATTENDANCE_PIN_RETIRED",
                    "message": "Reusable attendance PINs have been replaced by one-use clock-in and clock-out codes.",
                    "details": {
                        "endpoint": f"/api/businesses/{public_id}/workforce/me/attendance-code/"
                    },
                }
            },
            status=status.HTTP_410_GONE,
        )


class EmployeeAttendanceCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id)
        staff = employee_profile_for_user(request.user, business)
        if staff.employment_status != "active":
            return Response(
                {
                    "error": {
                        "code": "EMPLOYEE_APPROVAL_REQUIRED",
                        "message": "A manager must approve your employee profile before you can create an attendance code.",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        action = str(request.data.get("action", "")).strip()
        try:
            code, action_code = issue_attendance_action_code(staff, action)
        except ValueError as exc:
            return Response(
                {
                    "error": {
                        "code": "ATTENDANCE_ACTION_CONFLICT",
                        "message": str(exc),
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        record_audit(
            business,
            request.user,
            "staff.attendance_code_issued",
            "staff_profile",
            staff.public_id,
            {"action": action},
        )
        return Response(
            {
                "code": code,
                "action": action_code.action,
                "expires_at": action_code.expires_at,
                "message": "This code expires in five minutes and can be used once.",
            }
        )


class EmployeeLeaveRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id)
        staff = employee_profile_for_user(request.user, business)
        if staff.employment_status != "active":
            return Response(
                {
                    "error": {
                        "code": "EMPLOYEE_APPROVAL_REQUIRED",
                        "message": "Your employee profile must be active before requesting leave.",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        data = request.data.copy()
        data["staff_public_id"] = str(staff.public_id)
        data["status"] = "pending"
        serializer = LeaveRequestSerializer(
            data=data,
            context={"business": business, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        leave_request = serializer.save(
            business=business,
            staff=staff,
            status="pending",
            reviewed_by=None,
            reviewed_at=None,
        )
        record_audit(
            business,
            request.user,
            "leave_request.submitted",
            "leave_request",
            leave_request.public_id,
        )
        return Response(
            LeaveRequestSerializer(
                leave_request,
                context={"business": business, "request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeLeaveCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, leave_id):
        business = member_business(request.user, public_id)
        staff = employee_profile_for_user(request.user, business)
        leave_request = get_object_or_404(
            LeaveRequest,
            business=business,
            staff=staff,
            public_id=leave_id,
        )
        if leave_request.status != "pending":
            return Response(
                {
                    "error": {
                        "code": "LEAVE_REQUEST_CONFLICT",
                        "message": "Only pending leave requests can be cancelled.",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        leave_request.status = "cancelled"
        leave_request.save(update_fields=["status", "updated_at"])
        record_audit(
            business,
            request.user,
            "leave_request.cancelled",
            "leave_request",
            leave_request.public_id,
        )
        return Response(
            LeaveRequestSerializer(
                leave_request,
                context={"business": business, "request": request},
            ).data
        )


class EmployeeAdminSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id, staff_id):
        business = member_business(request.user, public_id, management=True)
        staff = get_object_or_404(
            StaffProfile.objects.select_related("membership", "business"),
            business=business,
            public_id=staff_id,
        )
        return Response(employee_summary_payload(staff, request))


class StaffAttendancePinView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, public_id, staff_id):
        business = member_business(request.user, public_id, management=True)
        staff = get_object_or_404(StaffProfile, business=business, public_id=staff_id)
        pin = issue_staff_pin(staff)
        record_audit(business, request.user, "staff.attendance_pin_issued", "staff_profile", staff.public_id)
        return Response({"attendance_pin": pin, "message": "Store this PIN securely. It is shown only once."})


class AttendanceTerminalView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        device = self.get_device(request)
        if not device:
            return self.access_denied_response()
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        logo_url = (
            request.build_absolute_uri(device.business.logo.url)
            if device.business.logo
            else None
        )
        return Response(
            {
                "device": {
                    "public_id": device.public_id,
                    "name": device.name,
                    "location_name": device.location.name if device.location else "Any location",
                },
                "business": {
                    "display_name": device.business.display_name,
                    "logo_url": logo_url,
                    "timezone": device.business.timezone,
                },
            }
        )

    def post(self, request):
        device = self.get_device(request)
        if not device:
            return self.access_denied_response()
        try:
            record, staff, action = consume_attendance_action_code(
                device,
                request.data.get("code"),
            )
        except ValueError as exc:
            return Response(
                {
                    "error": {
                        "code": "ATTENDANCE_CODE_INVALID",
                        "message": str(exc),
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        return Response(
            {
                "action": action,
                "employee_name": staff.display_name,
                "employee": {
                    "display_name": staff.display_name,
                    "job_title": staff.job_title,
                    "profile_image_url": (
                        request.build_absolute_uri(staff.profile_image.url)
                        if staff.profile_image
                        else None
                    ),
                },
                "record": AttendanceRecordSerializer(record).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def get_device(request):
        token = request.headers.get("X-Device-Token", "")
        return device_from_token(token, {"attendance"})

    @staticmethod
    def access_denied_response():
        return Response(
            {
                "error": {
                    "code": "DEVICE_ACCESS_DENIED",
                    "message": "Pair this attendance terminal again.",
                    "details": {},
                }
            },
            status=403,
        )
