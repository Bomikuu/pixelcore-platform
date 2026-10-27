from django.utils import timezone

from .services import rider_is_active


def rider_payload(rider):
    return {"public_id": str(rider.public_id), "display_name": rider.display_name, "email": rider.email, "kind": rider.kind, "status": rider.status, "available": rider_is_active(rider), "business_name": rider.business.display_name}


def delivery_payload(delivery, audience="owner"):
    order, rider = delivery.order, delivery.rider
    address, contact = order.shipping_snapshot or {}, order.customer_snapshot or {}
    active_rider = rider_is_active(rider)
    terminal = delivery.stage in {"delivered", "cancelled"} or order.status in {"fulfilled", "cancelled", "refunded"}
    location_allowed = not terminal and delivery.sharing and active_rider and delivery.stage == "out_for_delivery"
    point = None
    if location_allowed and delivery.received_at and delivery.latitude is not None and delivery.longitude is not None:
        point = {"latitude": delivery.latitude, "longitude": delivery.longitude, "accuracy": delivery.accuracy, "captured_at": delivery.captured_at, "received_at": delivery.received_at, "stale": (timezone.now() - delivery.received_at).total_seconds() > 90}
    destination = {"latitude": delivery.destination_latitude, "longitude": delivery.destination_longitude} if delivery.destination_latitude is not None and delivery.destination_longitude is not None else None
    result = {
        "public_id": str(delivery.public_id), "order_id": str(order.public_id), "order_number": order.number,
        "business_name": order.business.display_name, "business_slug": order.business.slug,
        "stage": delivery.stage, "revision": delivery.revision, "terminal": terminal,
        "rider": {"public_id": str(rider.public_id), "display_name": rider.display_name, "available": active_rider} if rider and (audience != "customer" or active_rider) else None,
        "destination": destination, "location": point, "sharing": location_allowed,
        "address": ", ".join(str(address[k]) for k in ("line1", "line2", "city", "region", "postal_code", "country") if address.get(k)),
        "events": [{"stage": e.stage, "message": e.message, "created_at": e.created_at} for e in delivery.events.all()],
        "placed_at": order.placed_at, "updated_at": delivery.updated_at,
    }
    if audience != "customer":
        result.update({"customer_name": " ".join(str(contact.get(k) or "") for k in ("first_name", "last_name")).strip() or "Customer", "customer_phone": str(contact.get("phone") or ""), "payment_status": order.payment_status, "payment_method": order.payment_method, "total": str(order.grand_total), "currency": order.currency, "items": [{"name": i.name, "quantity": i.quantity} for i in order.items.all()]})
    return result
