import base64
import hashlib
import secrets
from decimal import Decimal

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from businesses.google_calendar import sync_calendar_event
from businesses.models import BusinessEvent
from businesses.services import record_audit
from commerce.models import CartItem, Customer
from commerce.services import create_cart, create_order_from_cart
from .models import (
    Booking,
    BookingResource,
    Resource,
    ServiceSession,
    StaffProfile,
    VenueEvent,
)


class BookingConflict(Exception):
    pass


def booking_token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def event_access_token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _event_access_cipher():
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def read_event_access_token(instance, field_name):
    ciphertext_field = {
        "organizer_token_digest": "organizer_token_ciphertext",
        "invite_token_digest": "invite_token_ciphertext",
    }[field_name]
    ciphertext = getattr(instance, ciphertext_field, "")
    if not ciphertext:
        return ""
    try:
        return _event_access_cipher().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def issue_event_access_token(instance, field_name):
    token = secrets.token_urlsafe(32)
    ciphertext_field = {
        "organizer_token_digest": "organizer_token_ciphertext",
        "invite_token_digest": "invite_token_ciphertext",
    }[field_name]
    setattr(instance, field_name, event_access_token_digest(token))
    setattr(
        instance,
        ciphertext_field,
        _event_access_cipher().encrypt(token.encode("utf-8")).decode("utf-8"),
    )
    instance.save(update_fields=[field_name, ciphertext_field, "updated_at"])
    return token


def project_venue_event(event, actor=None):
    calendar_event = event.calendar_event or BusinessEvent(
        business=event.business,
        created_by=actor or event.business.created_by,
    )
    calendar_event.title = event.title
    calendar_event.notes = event.description
    calendar_event.event_type = "event"
    calendar_event.status = (
        "cancelled"
        if event.status == "cancelled"
        else "completed"
        if event.status == "completed"
        else "planned"
    )
    calendar_event.starts_at = event.starts_at
    calendar_event.ends_at = event.ends_at
    calendar_event.resource_layout = event.layout
    calendar_event.save()
    if event.calendar_event_id != calendar_event.id:
        VenueEvent.objects.filter(pk=event.pk).update(calendar_event=calendar_event)
        event.calendar_event = calendar_event
    sync_calendar_event(calendar_event)
    return calendar_event


def project_booking_event(booking, actor=None):
    if booking.status not in {"confirmed", "completed"}:
        if booking.event and booking.status == "cancelled":
            booking.event.status = "cancelled"
            booking.event.save(update_fields=["status", "updated_at"])
            sync_calendar_event(booking.event)
        return booking.event
    event = booking.event or BusinessEvent(
        business=booking.business,
        created_by=actor or booking.business.created_by,
    )
    event.title = f"{booking.offering.name} — {booking.customer.first_name or booking.customer.email}"
    event.notes = booking.customer_notes
    event.event_type = "appointment"
    event.status = "completed" if booking.status == "completed" else "planned"
    event.starts_at = booking.starts_at
    event.ends_at = booking.ends_at
    layout_ids = list(
        booking.resources.exclude(layout_id=None)
        .values_list("layout_id", flat=True)
        .distinct()[:2]
    )
    event.resource_layout_id = layout_ids[0] if len(layout_ids) == 1 else None
    event.save()
    if booking.event_id != event.id:
        booking.event = event
        booking.save(update_fields=["event", "updated_at"])
    sync_calendar_event(event)
    return event


@transaction.atomic
def create_booking(business, data, actor=None):
    payment_method = data.pop("payment_method", "paymongo")
    requires_approval = data.pop("requires_approval", False)
    data.pop("success_url", None)
    data.pop("cancel_url", None)
    offering = data["offering"]
    staff = data.get("staff")
    session = data.get("session")
    resources = data.pop("resources", [])
    if not staff and not session:
        for assignment in offering.staff_assignments.filter(is_active=True, staff__is_active=True, staff__is_bookable=True).select_related("staff"):
            candidate = assignment.staff
            if not Booking.objects.filter(
                business=business,
                staff=candidate,
                status__in=("pending", "confirmed"),
                starts_at__lt=data["ends_at"],
                ends_at__gt=data["starts_at"],
            ).exists():
                staff = candidate
                data["staff"] = candidate
                break
        if not staff:
            raise BookingConflict("No staff member is available at this time.")
    if staff:
        staff = StaffProfile.objects.select_for_update().get(pk=staff.pk)
    if session:
        session = ServiceSession.objects.select_for_update().get(pk=session.pk)
        occupied = session.bookings.filter(status__in=("pending", "confirmed")).aggregate(total=Sum("seats"))["total"] or 0
        if occupied + data.get("seats", 1) > session.capacity:
            raise BookingConflict("This session no longer has enough capacity.")
        data["starts_at"], data["ends_at"] = session.starts_at, session.ends_at
        data["staff"], data["location"] = session.staff, session.location
    elif staff and Booking.objects.filter(
        business=business,
        staff=staff,
        status__in=("pending", "confirmed"),
        starts_at__lt=data["ends_at"],
        ends_at__gt=data["starts_at"],
    ).exists():
        raise BookingConflict("The selected staff member is no longer available at this time.")
    locked_resources = []
    for resource in resources:
        locked = Resource.objects.select_for_update().get(pk=resource.pk, business=business, is_active=True)
        conflict = BookingResource.objects.filter(
            resource=locked,
            booking__status__in=("pending", "confirmed"),
            booking__starts_at__lt=data["ends_at"],
            booking__ends_at__gt=data["starts_at"],
        ).exists()
        if conflict:
            raise BookingConflict(f"{locked.name} is no longer available at this time.")
        locked_resources.append(locked)
    email = data.pop("email", "").lower().strip()
    customer_defaults = {
        "first_name": data.pop("first_name", ""),
        "last_name": data.pop("last_name", ""),
        "phone": data.pop("phone", ""),
    }
    if email:
        customer, _ = Customer.objects.get_or_create(
            business=business,
            email=email,
            defaults=customer_defaults,
        )
    else:
        customer = Customer.objects.create(
            business=business,
            email="",
            **customer_defaults,
        )
    token = secrets.token_urlsafe(32)
    payment_policy = data.get("payment_policy", "none")
    booking = Booking.objects.create(
        business=business,
        customer=customer,
        cancellation_token_digest=booking_token_digest(token),
        status="pending" if requires_approval or payment_policy != "none" else "confirmed",
        payment_status="not_required" if payment_policy == "none" else "unpaid",
        **data,
    )
    BookingResource.objects.bulk_create([BookingResource(booking=booking, resource=resource) for resource in locked_resources])
    if payment_policy != "none":
        cart, _ = create_cart(business)
        amount = offering.base_price
        if payment_policy == "deposit":
            if offering.metadata.get("deposit_amount") is not None:
                amount = Decimal(str(offering.metadata["deposit_amount"]))
            else:
                percentage = Decimal(str(offering.metadata.get("deposit_percent", 25)))
                amount = (offering.base_price * percentage / Decimal("100")).quantize(Decimal("0.01"))
        CartItem.objects.create(
            cart=cart,
            offering=offering,
            quantity=data.get("seats", 1),
            unit_price=amount,
            tax_rate=offering.tax_rate,
            metadata={"booking_public_id": str(booking.public_id), "payment_policy": payment_policy},
        )
        order = create_order_from_cart(cart, {
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone": customer.phone,
            "payment_method": payment_method,
            "fulfillment_type": "booking",
            "shipping_total": 0,
        })
        booking.order = order
        booking.save(update_fields=["order", "updated_at"])
    project_booking_event(booking, actor)
    record_audit(business, actor, "booking.created", "booking", booking.public_id)
    if booking.status == "confirmed":
        from .tasks import send_booking_confirmation
        transaction.on_commit(lambda: send_booking_confirmation.delay(booking.id))
    return booking, token


@transaction.atomic
def reschedule_booking(booking, starts_at, ends_at, actor=None):
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if booking.status not in {"pending", "confirmed"}:
        raise BookingConflict("Only pending or confirmed bookings can be rescheduled.")
    if ends_at <= starts_at or starts_at <= timezone.now():
        raise BookingConflict("Choose a future end time after the start time.")
    if booking.staff_id:
        StaffProfile.objects.select_for_update().get(pk=booking.staff_id)
        conflict = Booking.objects.filter(
            business=booking.business,
            staff=booking.staff,
            status__in=("pending", "confirmed"),
            starts_at__lt=ends_at,
            ends_at__gt=starts_at,
        ).exclude(pk=booking.pk).exists()
        if conflict:
            raise BookingConflict("The selected time is no longer available.")
    for resource in Resource.objects.select_for_update().filter(bookings=booking):
        conflict = BookingResource.objects.filter(
            resource=resource,
            booking__status__in=("pending", "confirmed"),
            booking__starts_at__lt=ends_at,
            booking__ends_at__gt=starts_at,
        ).exclude(booking=booking).exists()
        if conflict:
            raise BookingConflict(f"{resource.name} is no longer available at this time.")
    booking.starts_at, booking.ends_at = starts_at, ends_at
    booking.reminder_sent_at = None
    booking.save(update_fields=["starts_at", "ends_at", "reminder_sent_at", "updated_at"])
    project_booking_event(booking, actor)
    record_audit(booking.business, actor, "booking.rescheduled", "booking", booking.public_id)
    return booking
