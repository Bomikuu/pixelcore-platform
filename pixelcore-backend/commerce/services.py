import hashlib
import hmac
import json
import secrets
import time
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.core import signing
from django.utils import timezone

from businesses.google_calendar import decrypt_token, encrypt_token
from businesses.models import Business
from businesses.services import record_audit
from .models import Cart, Customer, DigitalDownloadGrant, Discount, Fulfillment, Order, OrderItem, PaymentAttempt, PaymentConnection, WebhookEvent


from .discounts import discount_amount


MONEY = Decimal("0.01")


class PaymentProviderError(Exception):
    pass


def digital_delivery_tokens(order):
    links = []
    for item in order.items.select_related("offering").filter(offering__offering_type="digital", offering__digital_asset__isnull=False):
        grant, _ = DigitalDownloadGrant.objects.get_or_create(
            order_item=item,
            defaults={"expires_at": timezone.now() + timedelta(days=7)},
        )
        token = signing.dumps({"grant": str(grant.public_id)}, salt="pixelcore-digital-download", compress=True)
        links.append({"name": item.name, "token": token})
    return links


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_cart(business):
    raw_token = secrets.token_urlsafe(32)
    cart = Cart.objects.create(
        business=business,
        access_token_digest=token_digest(raw_token),
        currency=business.currency,
        expires_at=timezone.now() + timedelta(days=14),
    )
    return cart, raw_token


def calculate_cart(cart, shipping_total=Decimal("0"), discount=None):
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for item in cart.items.all():
        line = item.unit_price * item.quantity
        subtotal += line
        rate = item.tax_rate / Decimal("100")
        if rate:
            tax_total += line - (line / (Decimal("1") + rate)) if cart.business.prices_include_tax else line * rate
    subtotal = subtotal.quantize(MONEY, rounding=ROUND_HALF_UP)
    tax_total = tax_total.quantize(MONEY, rounding=ROUND_HALF_UP)
    shipping_total = Decimal(shipping_total).quantize(MONEY, rounding=ROUND_HALF_UP)
    discount = discount or active_discount(cart.business)
    discount_total = discount_amount(discount, [
        (item.offering.public_id, item.unit_price * item.quantity)
        for item in cart.items.select_related("offering")
    ])
    grand_total = subtotal + shipping_total if cart.business.prices_include_tax else subtotal + tax_total + shipping_total
    grand_total = max(Decimal("0"), grand_total - discount_total)
    return {"subtotal": subtotal, "tax_total": tax_total, "shipping_total": shipping_total, "discount_total": discount_total, "grand_total": grand_total}


def active_discount(business, code=""):
    now = timezone.now()
    queryset = Discount.objects.filter(business=business, is_active=True).filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now)).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
    if code: return queryset.filter(code__iexact=code.strip()).first()
    return queryset.filter(is_automatic=True).first()


@transaction.atomic
def create_order_from_cart(cart, checkout_data):
    cart = Cart.objects.select_for_update().select_related("business").get(pk=cart.pk)
    if cart.status != "open" or cart.expires_at <= timezone.now() or not cart.items.exists():
        raise ValueError("This cart can no longer be checked out.")
    business = Business.objects.select_for_update().get(pk=cart.business_id)
    email = checkout_data["email"].lower().strip()
    customer, _ = Customer.objects.get_or_create(
        business=business,
        email=email,
        defaults={
            "first_name": checkout_data.get("first_name", ""),
            "last_name": checkout_data.get("last_name", ""),
            "phone": checkout_data.get("phone", ""),
        },
    )
    shipping_zone = checkout_data.get("shipping_zone")
    discount_code = checkout_data.pop("discount_code", "")
    discount = active_discount(business, discount_code) if discount_code else cart.discount
    if discount_code and not discount: raise ValueError("This discount code is invalid or expired.")
    totals = calculate_cart(cart, shipping_zone.flat_rate if shipping_zone else checkout_data.get("shipping_total", 0), discount)
    sequence = business.orders.count() + 1
    order = Order.objects.create(
        business=business,
        customer=customer,
        cart=cart,
        number=f"ORD-{timezone.localdate().year}-{sequence:06d}",
        payment_method=checkout_data["payment_method"],
        payment_status="pending" if checkout_data["payment_method"] == "paymongo" else "unpaid",
        status="confirmed" if checkout_data["payment_method"] in {"cod", "manual"} else "pending",
        fulfillment_type=checkout_data.get("fulfillment_type", ""),
        currency=business.currency,
        customer_snapshot={"email": email, "first_name": checkout_data.get("first_name", ""), "last_name": checkout_data.get("last_name", ""), "phone": checkout_data.get("phone", "")},
        shipping_snapshot=checkout_data.get("shipping_address", {}),
        **totals,
    )
    for item in cart.items.select_related("offering", "variant").prefetch_related("offering__cost_components"):
        component_cost = sum((component.quantity * component.unit_cost for component in item.offering.cost_components.all()), Decimal("0"))
        option_cost = sum((Decimal(str(option.get("cost_delta", "0"))) for option in item.metadata.get("options", [])), Decimal("0"))
        unit_cost = (item.variant.unit_cost if item.variant else component_cost) + option_cost
        OrderItem.objects.create(
            order=order,
            offering=item.offering,
            variant=item.variant,
            name=item.offering.name,
            sku=item.variant.sku if item.variant else item.offering.sku,
            quantity=item.quantity,
            unit_price=item.unit_price,
            tax_rate=item.tax_rate,
            line_total=(item.unit_price * item.quantity).quantize(MONEY),
            offering_snapshot={"type": item.offering.offering_type, "fulfillment_type": item.offering.fulfillment_type, "unit_cost": str(unit_cost), "metadata": item.offering.metadata, "selected_options": item.metadata.get("options", []), "note": item.metadata.get("note", "")},
        )
    Fulfillment.objects.create(order=order, fulfillment_type=order.fulfillment_type or "none")
    cart.status = "converted"
    cart.customer = customer
    cart.email = email
    cart.save(update_fields=["status", "customer", "email", "updated_at"])
    if not business.currency_locked_at:
        business.currency_locked_at = timezone.now()
        business.save(update_fields=["currency_locked_at", "updated_at"])
    try:
        from operations.services import reserve_order_stock
        reserve_order_stock(order)
    except ImportError:
        pass
    record_audit(business, None, "order.placed", "order", order.public_id, {"number": order.number})
    return order


def configure_payment_connection(business, provider, secret_key, webhook_secret, public_key="", is_live=False):
    return PaymentConnection.objects.update_or_create(
        business=business,
        provider=provider,
        defaults={
            "encrypted_secret_key": encrypt_token(secret_key),
            "encrypted_webhook_secret": encrypt_token(webhook_secret),
            "public_key": public_key,
            "is_live": is_live,
            "is_active": True,
        },
    )[0]


def create_paymongo_checkout(order, success_url, cancel_url, idempotency_key):
    existing = PaymentAttempt.objects.filter(business=order.business, idempotency_key=idempotency_key).first()
    if existing:
        return existing
    connection = PaymentConnection.objects.filter(business=order.business, provider="paymongo", is_active=True).first()
    if not connection:
        raise PaymentProviderError("PayMongo is not connected for this business.")
    attempt = PaymentAttempt.objects.create(
        business=order.business,
        order=order,
        provider="paymongo",
        amount=order.grand_total,
        currency=order.currency,
        idempotency_key=idempotency_key,
    )
    line_items = [
        {"name": item.name, "amount": int(item.unit_price * 100), "currency": order.currency, "quantity": item.quantity}
        for item in order.items.all()
    ]
    if order.tax_total and not order.business.prices_include_tax:
        line_items.append({"name": "Tax", "amount": int(order.tax_total * 100), "currency": order.currency, "quantity": 1})
    if order.shipping_total:
        line_items.append({"name": "Shipping", "amount": int(order.shipping_total * 100), "currency": order.currency, "quantity": 1})
    payload = {
        "data": {
            "attributes": {
                "line_items": line_items,
                "payment_method_types": ["card", "gcash", "paymaya", "qrph"],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "reference_number": order.number,
                "description": f"Order {order.number}",
            }
        }
    }
    try:
        response = requests.post(
            "https://api.paymongo.com/v2/checkout_sessions",
            auth=(decrypt_token(connection.encrypted_secret_key), ""),
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
            timeout=20,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        attempt.status = "failed"
        attempt.save(update_fields=["status", "updated_at"])
        raise PaymentProviderError("PayMongo could not create a checkout session.") from exc
    if not response.ok:
        attempt.status = "failed"
        attempt.raw_status = data
        attempt.save(update_fields=["status", "raw_status", "updated_at"])
        raise PaymentProviderError("PayMongo rejected the checkout request.")
    attributes = data["data"]["attributes"]
    attempt.provider_reference = data["data"]["id"]
    attempt.checkout_url = attributes["checkout_url"]
    attempt.status = "pending"
    attempt.raw_status = data
    attempt.save(update_fields=["provider_reference", "checkout_url", "status", "raw_status", "updated_at"])
    return attempt


def verify_paymongo_signature(raw_body, signature_header, secret, live=False, replay_seconds=300):
    parts = dict(part.strip().split("=", 1) for part in signature_header.split(",") if "=" in part)
    timestamp = parts.get("t", "")
    supplied = parts.get("li" if live else "te", "")
    if not timestamp.isdigit() or abs(int(time.time()) - int(timestamp)) > replay_seconds:
        return False
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + raw_body, hashlib.sha256).hexdigest()
    return bool(supplied) and hmac.compare_digest(supplied, expected)


@transaction.atomic
def process_paymongo_webhook(business, raw_body, signature_header):
    connection = PaymentConnection.objects.get(business=business, provider="paymongo", is_active=True)
    secret = decrypt_token(connection.encrypted_webhook_secret)
    if not verify_paymongo_signature(raw_body, signature_header, secret, connection.is_live):
        raise PaymentProviderError("Webhook signature is invalid or expired.")
    payload = json.loads(raw_body)
    data = payload.get("data", {})
    event_id = str(data.get("id", ""))
    event_type = str(data.get("attributes", {}).get("type", ""))
    if not event_id or not event_type:
        raise PaymentProviderError("Webhook payload is missing its event identity.")
    try:
        WebhookEvent.objects.create(business=business, provider="paymongo", event_id=event_id, event_type=event_type, payload=payload)
    except IntegrityError:
        return None
    if event_type == "checkout_session.payment.paid":
        provider_reference = data.get("attributes", {}).get("data", {}).get("id", "")
        attempt = PaymentAttempt.objects.select_for_update().select_related("order").filter(
            business=business,
            provider="paymongo",
            provider_reference=provider_reference,
        ).first()
        order = Order.objects.select_for_update().filter(pk=attempt.order_id, business=business).first() if attempt else None
        if order:
            order.payment_status = "paid"
            order.status = "confirmed"
            order.save(update_fields=["payment_status", "status", "updated_at"])
            attempt.status = "paid"
            attempt.save(update_fields=["status", "updated_at"])
            booking = order.bookings.select_related("business", "customer", "offering").first()
            if booking:
                booking.payment_status = "paid"
                booking.status = "confirmed"
                booking.save(update_fields=["payment_status", "status", "updated_at"])
                from scheduling.services import project_booking_event
                project_booking_event(booking)
            if digital_delivery_tokens(order):
                from .tasks import send_digital_delivery
                transaction.on_commit(lambda: send_digital_delivery.delay(order.id))
            record_audit(business, None, "payment.confirmed", "order", order.public_id, {"provider": "paymongo"})
            return order
    return None
