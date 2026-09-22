import secrets
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from businesses.services import record_audit
from scheduling.models import StaffProfile
from .models import AttendanceActionCode, AttendanceFlag, AttendanceRecord


ATTENDANCE_CODE_LENGTH = 6


def pin_digest(staff, pin):
    return signing.salted_hmac("pixelcore.attendance-pin", f"{staff.public_id}:{pin}", secret=settings.SECRET_KEY).hexdigest()


def issue_staff_pin(staff):
    pin = f"{secrets.randbelow(1_000_000):06d}"
    staff.attendance_pin_digest = pin_digest(staff, pin)
    staff.attendance_pin_generated_at = timezone.now()
    staff.save(update_fields=["attendance_pin_digest", "attendance_pin_generated_at", "updated_at"])
    return pin


def verify_staff_pin(staff, pin):
    return bool(staff.attendance_pin_digest) and secrets.compare_digest(staff.attendance_pin_digest, pin_digest(staff, pin))


def attendance_code_digest(code):
    return signing.salted_hmac(
        "pixelcore.attendance-action-code",
        code,
        secret=settings.SECRET_KEY,
    ).hexdigest()


@transaction.atomic
def issue_attendance_action_code(staff, action):
    if action not in {"clock_in", "clock_out"}:
        raise ValueError("Choose clock_in or clock_out.")

    staff = StaffProfile.objects.select_for_update().get(
        pk=staff.pk,
        employment_status="active",
        is_active=True,
    )
    is_clocked_in = staff.attendance_records.filter(
        clock_in__isnull=False,
        clock_out__isnull=True,
    ).exists()
    if action == "clock_in" and is_clocked_in:
        raise ValueError("You are already clocked in. Generate a clock-out code instead.")
    if action == "clock_out" and not is_clocked_in:
        raise ValueError("You are not clocked in. Generate a clock-in code instead.")

    now = timezone.now()
    staff.attendance_action_codes.filter(
        consumed_at__isnull=True,
        expires_at__gt=now,
    ).update(consumed_at=now)

    for _ in range(12):
        code = f"{secrets.randbelow(10 ** ATTENDANCE_CODE_LENGTH):0{ATTENDANCE_CODE_LENGTH}d}"
        digest = attendance_code_digest(code)
        collision = AttendanceActionCode.objects.filter(
            business=staff.business,
            code_digest=digest,
            consumed_at__isnull=True,
            expires_at__gt=now,
        ).exists()
        if not collision:
            action_code = AttendanceActionCode.objects.create(
                business=staff.business,
                staff=staff,
                action=action,
                code_digest=digest,
            )
            return code, action_code

    raise RuntimeError("A unique attendance code could not be created. Try again.")


@transaction.atomic
def consume_attendance_action_code(device, code):
    normalized_code = str(code or "").strip()
    if len(normalized_code) != ATTENDANCE_CODE_LENGTH or not normalized_code.isdigit():
        raise ValueError("Enter the six-digit code from your employee portal.")

    now = timezone.now()
    action_code = (
        AttendanceActionCode.objects.select_for_update()
        .select_related("staff")
        .filter(
            business=device.business,
            code_digest=attendance_code_digest(normalized_code),
            consumed_at__isnull=True,
            expires_at__gt=now,
            staff__employment_status="active",
            staff__is_active=True,
        )
        .first()
    )
    if not action_code:
        raise ValueError("This attendance code is invalid, expired, or already used.")

    record = clock_staff(device, action_code.staff, action_code.action)
    action_code.consumed_at = now
    action_code.save(update_fields=["consumed_at"])
    return record, action_code.staff, action_code.action


@transaction.atomic
def clock_staff(device, staff, action):
    staff = StaffProfile.objects.select_for_update().get(pk=staff.pk, business=device.business, employment_status="active")
    now = timezone.now()
    if action == "clock_in":
        if staff.attendance_records.filter(clock_in__isnull=False, clock_out__isnull=True).exists():
            raise ValueError("This staff member is already clocked in.")
        scheduled_start = None
        late_minutes = 0
        if staff.scheduled_start_time:
            try: zone = ZoneInfo(staff.timezone)
            except ZoneInfoNotFoundError: zone = ZoneInfo("Asia/Manila")
            scheduled_start = datetime.combine(timezone.localdate(now, zone), staff.scheduled_start_time, tzinfo=zone)
            late_minutes = max(0, int((now - scheduled_start).total_seconds() // 60) - staff.late_grace_minutes)
        record = AttendanceRecord.objects.create(business=device.business, staff=staff, location=device.location, clock_in=now, scheduled_start=scheduled_start, late_minutes=late_minutes, status="late" if late_minutes else "present")
        recent_lates = staff.attendance_records.filter(status="late").order_by("-clock_in")[:staff.consecutive_late_threshold]
        recent_lates = list(recent_lates)
        if len(recent_lates) >= staff.consecutive_late_threshold:
            AttendanceFlag.objects.get_or_create(business=device.business, staff=staff, flag_type="consecutive_late", status="open", defaults={"occurrence_count": len(recent_lates), "first_occurrence": recent_lates[-1].clock_in.date(), "last_occurrence": recent_lates[0].clock_in.date(), "summary": f"{len(recent_lates)} consecutive late arrivals"})
    elif action == "clock_out":
        record = staff.attendance_records.select_for_update().filter(clock_in__isnull=False, clock_out__isnull=True).first()
        if not record: raise ValueError("This staff member is not clocked in.")
        record.clock_out = now
        record.save(update_fields=["clock_out", "updated_at"])
    else:
        raise ValueError("Choose clock_in or clock_out.")
    record_audit(device.business, None, f"attendance.{action}", "attendance_record", record.public_id, {"device": str(device.public_id), "staff": str(staff.public_id)})
    return record
