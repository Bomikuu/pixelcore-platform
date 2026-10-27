"""Delivery authorization and lifecycle. Mutations lock Order before Delivery."""
import math
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from businesses.models import BusinessMembership
from commerce.models import Fulfillment, Order
from .models import Delivery, DeliveryEvent, RiderAccess

TERMINAL = {"delivered", "cancelled"}


class DeliveryConflict(APIException):
    status_code = 409
    default_detail = "This delivery changed. Refresh and try again."


def verified_email(user):
    profile = getattr(user, "account_profile", None)
    return user.email.strip().lower() if user.is_authenticated and profile and profile.email_verified_at else ""


def rider_is_active(rider):
    if not rider or rider.status != "active" or not rider.user_id or not rider.user.is_active or rider.business.status != "active":
        return False
    return rider.kind != "employee" or BusinessMembership.objects.filter(business_id=rider.business_id, user_id=rider.user_id, status="active").exists()


def rider_access_query(user):
    query = Q(user=user)
    email = verified_email(user)
    if email:
        query |= Q(email=email, status="invited", kind="independent")
    return RiderAccess.objects.filter(query, business__status="active").select_related("business", "user")


def has_delivery_access(user):
    return any(r.status == "invited" or rider_is_active(r) for r in rider_access_query(user))


def clear_location(delivery):
    delivery.sharing = False
    for field in ("latitude", "longitude", "accuracy", "captured_at", "received_at"):
        setattr(delivery, field, None)


def coordinates(latitude, longitude):
    try:
        lat, lng = float(latitude), float(longitude)
    except (ValueError, TypeError, OverflowError):
        raise ValidationError({"coordinates": "Choose a valid latitude and longitude."})
    if not math.isfinite(lat) or not math.isfinite(lng) or not -90 <= lat <= 90 or not -180 <= lng <= 180:
        raise ValidationError({"coordinates": "Latitude must be −90 to 90 and longitude −180 to 180."})
    return lat, lng


def ensure_delivery(order):
    if order.fulfillment_type != "delivery":
        return None
    terminal_stage = "delivered" if order.status == "fulfilled" else "cancelled" if order.status in {"cancelled", "refunded"} else None
    ready = order.fulfillments.filter(fulfillment_type="delivery", status="ready").exists()
    stage = terminal_stage or ("ready" if ready else "preparing")
    delivery, created = Delivery.objects.get_or_create(order=order, defaults={"stage": stage})
    if created:
        snapshot = order.shipping_snapshot or {}
        try:
            delivery.destination_latitude, delivery.destination_longitude = coordinates(snapshot.get("latitude"), snapshot.get("longitude"))
            delivery.save()
        except ValidationError:
            pass
        DeliveryEvent.objects.create(delivery=delivery, stage=stage, message="Delivery recorded")
    elif (terminal_stage and delivery.stage != terminal_stage) or (stage == "ready" and delivery.stage == "preparing"):
        delivery.stage = stage
        delivery.revision += 1
        if stage in TERMINAL:
            clear_location(delivery)
        delivery.save()
        DeliveryEvent.objects.create(delivery=delivery, stage=stage, message="Order " + stage.replace("_", " "))
    return delivery


def locked_delivery(public_id, queryset):
    """Called inside an atomic block; repeat authorization after waiting for locks."""
    from django.shortcuts import get_object_or_404
    row = get_object_or_404(queryset, public_id=public_id)
    Order.objects.select_for_update().get(pk=row.order_id)
    return get_object_or_404(queryset.select_for_update(of=("self",)), public_id=public_id)


def check_revision(delivery, revision):
    if revision != delivery.revision:
        raise DeliveryConflict()
    if delivery.stage in TERMINAL or delivery.order.status in {"fulfilled", "cancelled", "refunded"}:
        raise DeliveryConflict("This delivery is already closed.")


def transition(delivery, stage, user):
    allowed = {"preparing": {"ready", "cancelled"}, "ready": {"out_for_delivery", "cancelled"}, "out_for_delivery": {"delivered", "cancelled"}}
    if stage not in allowed.get(delivery.stage, set()):
        raise DeliveryConflict("That status change is unavailable. Refresh the delivery.")
    if stage == "out_for_delivery" and not rider_is_active(delivery.rider):
        raise ValidationError({"rider": "Assign an active rider before dispatching."})
    order = delivery.order
    fulfillment = Fulfillment.objects.filter(order=order, fulfillment_type="delivery").first()
    if not fulfillment:
        fulfillment = Fulfillment.objects.create(order=order, fulfillment_type="delivery")
    if stage == "delivered":
        from operations.services import commit_order_stock
        try:
            commit_order_stock(order, user)
        except ValueError as exc:
            raise ValidationError({"inventory": str(exc)}) from exc
        order.status = "fulfilled"
        fulfillment.status = "fulfilled"
        fulfillment.fulfilled_at = timezone.now()
    elif stage == "cancelled":
        from operations.services import release_order_stock
        release_order_stock(order)
        order.status = "cancelled"
        fulfillment.status = "cancelled"
    else:
        order.status = "processing"
        fulfillment.status = "ready"
    delivery.stage = stage
    delivery.revision += 1
    if stage in TERMINAL:
        clear_location(delivery)
    delivery.save()
    DeliveryEvent.objects.create(delivery=delivery, stage=stage, message=stage.replace("_", " ").capitalize())
    fulfillment.save(update_fields=["status", "fulfilled_at"])
    order.save(update_fields=["status", "updated_at"])


def receive_location(delivery, data):
    if not delivery.sharing or delivery.stage != "out_for_delivery":
        raise DeliveryConflict("Start location sharing on an active delivery first.")
    lat, lng = coordinates(data["latitude"], data["longitude"])
    accuracy = data["accuracy"]
    if not math.isfinite(accuracy) or accuracy < 0 or accuracy > 10000:
        raise ValidationError({"accuracy": "GPS accuracy must be between 0 and 10,000 metres."})
    captured_at, now = data["captured_at"], timezone.now()
    if captured_at < now - timedelta(seconds=120) or captured_at > now + timedelta(seconds=15):
        raise ValidationError({"captured_at": "This GPS fix is too old or ahead of server time. Request a fresh position."})
    if delivery.captured_at and captured_at <= delivery.captured_at:
        raise DeliveryConflict("A newer GPS position has already been received.")
    if delivery.received_at and (now - delivery.received_at).total_seconds() < 30:
        return False
    delivery.latitude, delivery.longitude = lat, lng
    delivery.accuracy, delivery.captured_at, delivery.received_at = accuracy, captured_at, now
    delivery.save(update_fields=["latitude", "longitude", "accuracy", "captured_at", "received_at", "updated_at"])
    return True
