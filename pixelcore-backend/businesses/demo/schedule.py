"""Bookings, events and workforce history without integrations or notifications."""

from datetime import time, timedelta

from businesses.models import BusinessEvent
from scheduling.models import (
    Booking, BookingResource, EventGuest, EventMedia, Resource, ResourceLayout,
    ResourceType, SchedulingSettings, VenueEvent,
)
from workforce.models import AttendanceFlag, AttendanceRecord, LeaveRequest


def calendar_entry(ctx, related, field, **fields):
    event = getattr(related, field)
    if event is None:
        event = BusinessEvent.objects.create(business=ctx.business, created_by=ctx.owner, **fields)
        setattr(related, field, event)
        related.save(update_fields=[field])
    else:
        for key, value in fields.items():
            setattr(event, key, value)
        event.save(update_fields=list(fields))
    return event


def import_schedule(ctx):
    SchedulingSettings.objects.update_or_create(business=ctx.business, defaults={
        "public_booking_enabled": True, "public_intro": "Book a shopping consultation or a practical Northline workshop.", "advance_booking_days": 31})
    kind = ctx.save(ResourceType, "resource-type:studio", business=ctx.business, name="Studio space",
                    singular_label="Studio space", plural_label="Studio spaces", icon="door-open")
    layout = ctx.save(ResourceLayout, "layout:studio", business=ctx.business, location=ctx.location,
        name="Northline studio", layout_type="event", description="A fictional studio for appointments and small gatherings.")
    resources = [ctx.save(Resource, f"room:{i}", business=ctx.business, resource_type=kind,
                         location=ctx.location, layout=layout, name=f"Consultation space {i + 1}",
                         element_type="service", capacity=2, position_x=20 + i * 35, position_y=35,
                         shape="rectangle", width=25, height=20) for i in range(3)]
    slots = [ctx.at(day, hour) for day in range(1, ctx.days + 1)
             if ctx.at(day).weekday() < 6 for hour in (10, 14)]
    for row in ctx.data["bookings"]:
        start = slots[round(row["position"] * (len(slots) - 1))]
        service = ctx.services[row["service"]]
        end = start + timedelta(minutes=service.duration_minutes)
        status = row["historical_status"] if end < ctx.now else row["future_status"]
        booking = ctx.save(Booking, ctx.monthly(row["id"]), business=ctx.business,
            customer=ctx.customers[row["customer"]], offering=service, staff=ctx.staff[row["staff"]],
            location=ctx.location, status=status, starts_at=start, ends_at=end, timezone="Asia/Manila",
            seats=1, payment_policy="none", payment_status="not_required", cancellation_token_digest="",
            customer_notes="Fictional appointment for the monthly demonstration.",
            cancelled_at=min(start, ctx.now) if status == "cancelled" else None)
        created = max(ctx.first, min(start - timedelta(days=2), ctx.now))
        ctx.stamp(booking, created_at=created, updated_at=min(end, ctx.now))
        resource = resources[["staff-02", "staff-03", "staff-08"].index(row["staff"])]
        BookingResource.objects.update_or_create(booking=booking, resource=resource, defaults={"quantity": 1})
        event = calendar_entry(ctx, booking, "event", title=f"{service.name} — {booking.customer.first_name}",
            event_type="appointment", starts_at=start, ends_at=end, resource_layout=layout,
            status="completed" if status == "completed" else "cancelled" if status in {"cancelled", "no_show"} else "planned",
            notes="Fictional appointment; no Google Calendar synchronization was requested.")
        ctx.stamp(event, created_at=created, updated_at=min(end, ctx.now))
    for row in ctx.data["events"]:
        start = ctx.at(row["day"], 18)
        event = ctx.save(VenueEvent, ctx.monthly(row["id"]), business=ctx.business,
            title=row["title"], event_type=row["event_type"], status="completed" if start + timedelta(hours=2) < ctx.now else "open",
            starts_at=start, ends_at=start + timedelta(hours=2), location=ctx.location, layout=layout,
            handler=ctx.staff["staff-08"], organizer_name="Northline demonstration team",
            organizer_email="events@example.test", description=row["description"], max_guests=30,
            created_by=ctx.owner, public_rsvp_enabled=True, website_enabled=True,
            website_template="general_community", header_mark_text="Northline Studio", website_published_at=ctx.first,
            theme_background="#F6F1E8", theme_text="#253029", theme_accent="#65735A",
            thumbnail=ctx.assets["event-venue"].file.name)
        event.assigned_staff.set([ctx.staff["staff-07"], ctx.staff["staff-08"]])
        event.products.set(ctx.products.values())
        ctx.save(EventMedia, ctx.monthly(f"{row['id']}:hero"), event=event,
            image=ctx.assets["event-venue"].file.name, placement="hero", is_featured=True,
            alt_text="Original AI-generated Northline event venue photograph", caption="Fictional demonstration venue")
        calendar_entry(ctx, event, "calendar_event", title=event.title, event_type="event", starts_at=start,
                       ends_at=event.ends_at, resource_layout=layout,
                       status="completed" if event.status == "completed" else "planned", notes=event.description)
        for index, customer in enumerate(list(ctx.customers.values())[:8]):
            response = ["accepted", "accepted", "accepted", "pending", "declined", "maybe", "accepted", "pending"][index]
            ctx.save(EventGuest, ctx.monthly(f"{row['id']}:guest:{index}"), event=event,
                full_name=f"{customer.first_name} {customer.last_name}", email=customer.email,
                phone=customer.phone, party_size=1 + index % 2, response=response,
                responded_at=min(ctx.now, start) if response != "pending" else None,
                dietary_notes="Vegetarian meal requested" if index == 0 else "")


def import_workforce(ctx):
    leave_dates = {}
    for row in ctx.data["leave_requests"]:
        start = ctx.at(row["day"]).date()
        end = min(start + timedelta(days=row["length"] - 1), ctx.first.replace(day=ctx.days).date())
        leave = ctx.save(LeaveRequest, ctx.monthly(row["id"]), business=ctx.business,
            staff=ctx.staff[row["staff"]], leave_type=row["type"], start_date=start, end_date=end,
            reason=row["reason"], status=row["status"], reviewed_by=ctx.owner if row["status"] == "approved" else None,
            reviewed_at=min(ctx.at(row["day"]), ctx.now) if row["status"] == "approved" else None,
            review_notes="Fictional workforce example.")
        ctx.stamp(leave, created_at=max(ctx.first, min(ctx.at(row["day"]) - timedelta(days=3), ctx.now)))
        if row["status"] == "approved":
            for offset in range((end - start).days + 1):
                leave_dates[(row["staff"], start + timedelta(days=offset))] = True
    workdays = [day for day in range(1, ctx.history_days + 1)
                if ctx.at(day).weekday() in ctx.data["attendance"]["weekdays"]]
    late_dates = []
    for index, day in enumerate(workdays):
        scheduled = ctx.at(day, 9)
        if scheduled > ctx.now:
            continue
        for key, staff in ctx.staff.items():
            on_leave = (key, scheduled.date()) in leave_dates
            late = key == ctx.data["attendance"]["late_staff"] and index in ctx.data["attendance"]["late_workday_indices"] and not on_leave
            minutes = ctx.data["attendance"]["late_minutes"] if late else 0
            clock_in = scheduled + timedelta(minutes=minutes)
            if not on_leave and clock_in > ctx.now:
                continue
            end = ctx.at(day, 18)
            status = "leave" if on_leave else "late" if late else "present"
            record = ctx.save(AttendanceRecord, ctx.monthly(f"attendance:{key}:{day}"), business=ctx.business,
                staff=staff, location=ctx.location, scheduled_start=scheduled,
                clock_in=None if on_leave else clock_in,
                clock_out=None if on_leave or end > ctx.now else end,
                status=status, late_minutes=minutes, late_reason="Fictional transport delay" if late else "",
                notes="Fictional monthly attendance record.")
            ctx.stamp(record, created_at=scheduled, updated_at=min(end, ctx.now))
            if late:
                late_dates.append(scheduled.date())
    if len(late_dates) >= 3:
        flag = ctx.save(AttendanceFlag, ctx.monthly("late-flag"), business=ctx.business,
            staff=ctx.staff[ctx.data["attendance"]["late_staff"]], flag_type="consecutive_late",
            status="open" if ctx.month == ctx.now.strftime("%Y-%m") else "resolved", occurrence_count=len(late_dates),
            first_occurrence=min(late_dates), last_occurrence=max(late_dates),
            summary="Three consecutive scheduled workdays with late clock-ins (demo).")
        ctx.stamp(flag, created_at=ctx.at(max(late_dates).day, 10))
