"""Inventory-backed product requests. Lock order: business, request, balance."""
import hashlib
import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException

from businesses.models import Business, BusinessLocation
from businesses.services import record_audit
from catalog.models import Offering, OfferingVariant
from operations.models import InventoryBalance
from .models import CartItem, ProductRequest, ProductRequestSettings
from .services import create_cart, create_order_from_cart


class RequestConflict(APIException):
    status_code = 409
    default_code = "PRODUCT_REQUEST_CONFLICT"


class ProductRequestInput(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    offering_public_id = serializers.UUIDField()
    variant_public_id = serializers.UUIDField()
    location_public_id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=["reservation", "rental"])
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    email = serializers.EmailField()
    phone = serializers.RegexField(r"^[0-9+().\-\s]{5,32}$")
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
    starts_on = serializers.DateField(required=False)
    ends_on = serializers.DateField(required=False)
    accepts_terms = serializers.BooleanField()

    def validate(self, attrs):
        if not attrs["accepts_terms"]:
            raise serializers.ValidationError({"accepts_terms": "Please acknowledge the request terms."})
        if attrs["kind"] == "rental":
            today = timezone.now().astimezone(ZoneInfo(self.context["business"].timezone)).date()
            start, end = attrs.get("starts_on"), attrs.get("ends_on")
            if not start or not end or start < today or end < start or (end - start).days > 365:
                raise serializers.ValidationError({"starts_on": "Choose a future rental range of up to 366 days."})
        elif attrs.get("starts_on") or attrs.get("ends_on"):
            raise serializers.ValidationError("Stock reservations use the business hold deadline, not a rental date range.")
        attrs["email"] = attrs["email"].lower()
        return attrs


class ProductRequestSettingsSerializer(serializers.ModelSerializer):
    hold_hours = serializers.IntegerField(min_value=1, max_value=168)

    class Meta:
        model = ProductRequestSettings
        fields = ["reservation_enabled", "rental_enabled", "hold_hours"]


class ProductRequestSerializer(serializers.ModelSerializer):
    attention = serializers.SerializerMethodField()
    location_name = serializers.CharField(source="location.name", read_only=True)
    order_public_id = serializers.UUIDField(source="order.public_id", read_only=True, allow_null=True)
    order_number = serializers.CharField(source="order.number", read_only=True, allow_null=True)

    class Meta:
        model = ProductRequest
        fields = ["public_id", "kind", "status", "quantity", "first_name", "last_name", "email", "phone", "notes", "decision_note", "starts_on", "ends_on", "expires_at", "stock_held", "snapshot", "location_name", "order_public_id", "order_number", "created_at", "updated_at", "attention"]
        read_only_fields = fields

    def get_attention(self, obj):
        from .live_sales import local_today
        today = local_today(obj.business)
        if obj.kind == 'rental' and obj.status == 'collected' and obj.ends_on:
            days = (today - obj.ends_on).days
            if days > 0:
                return {'code': 'overdue', 'days': days, 'label': f'{days} day' + ('s' if days != 1 else '') + ' overdue'}
            if days == 0:
                return {'code': 'due_today', 'days': 0, 'label': 'Return due today'}
        if obj.kind == 'rental' and obj.status == 'approved' and obj.starts_on and obj.starts_on < today:
            return {'code': 'missed_pickup', 'days': (today - obj.starts_on).days, 'label': 'Collection overdue'}
        if obj.status == 'pending':
            return {'code': 'approval', 'days': 0, 'label': 'Awaiting review'}
        return None


def request_options(offering):
    profile = getattr(offering, "product_profile", None)
    config = getattr(offering.business, "product_request_settings", None)
    eligible = offering.offering_type == "physical" and offering.track_inventory and profile and config
    reservation = bool(eligible and config.reservation_enabled and profile.reservation_enabled)
    rental = bool(eligible and config.rental_enabled and profile.rental_enabled)
    result = {"reservation_enabled": reservation, "rental_enabled": rental}
    if reservation or rental:
        result.update({
            "hold_hours": config.hold_hours,
            "reservation_terms": profile.reservation_terms,
            "rental_terms": profile.rental_terms,
            "locations": [{"public_id": str(item.public_id), "name": item.name, "address": item.address}
                          for item in offering.business.locations.filter(is_active=True)],
        })
    return result


def public_request_result(item):
    # No contact details, private inventory, or another customer's order in guest responses.
    return {"public_id": str(item.public_id), "kind": item.kind, "status": item.status,
            "quantity": item.quantity, "expires_at": item.expires_at, "starts_on": item.starts_on,
            "ends_on": item.ends_on, "snapshot": item.snapshot, "location_name": item.location.name}


def release_request_stock(item):
    if item.stock_held:
        balance = InventoryBalance.objects.select_for_update().get(pk=item.balance_id)
        if balance.reserved < item.quantity:
            raise RequestConflict("Inventory needs review before this request can be released.")
        balance.reserved -= item.quantity
        balance.save(update_fields=["reserved", "updated_at"])
        item.stock_held = False


@transaction.atomic
def expire_business_requests(business_id):
    Business.objects.select_for_update().get(pk=business_id)
    expired = ProductRequest.objects.select_for_update().filter(business_id=business_id, kind="reservation", status="held", expires_at__lte=timezone.now())
    count = 0
    for item in expired:
        release_request_stock(item)
        item.status = "expired"
        item.save(update_fields=["status", "stock_held", "updated_at"])
        record_audit(item.business, None, "product_request.expired", "product_request", item.public_id)
        count += 1
    return count


def release_expired_product_requests():
    ids = ProductRequest.objects.filter(kind="reservation", status="held", expires_at__lte=timezone.now()).order_by().values_list("business_id", flat=True).distinct()
    return sum(expire_business_requests(pk) for pk in list(ids))


def hold_request_stock(item):
    balance = InventoryBalance.objects.select_for_update().filter(business=item.business, variant=item.variant, location=item.location).first()
    if not balance or balance.available < item.quantity:
        raise RequestConflict("There are not enough available units at this location. Choose another location or quantity.")
    balance.reserved += item.quantity
    balance.save(update_fields=["reserved", "updated_at"])
    item.balance = balance
    item.stock_held = True


@transaction.atomic
def create_product_request(business, data):
    business = Business.objects.select_for_update().get(pk=business.pk)
    payload = {key: value for key, value in data.items() if key != "idempotency_key"}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    key = hashlib.sha256(str(data["idempotency_key"]).encode()).hexdigest()
    existing = ProductRequest.objects.filter(business=business, idempotency_digest=key).first()
    if existing:
        if existing.payload_digest != digest:
            raise RequestConflict("This request key was already used with different details. Start a new request.")
        return existing, False
    offering = get_object_or_404(Offering, business=business, public_id=data["offering_public_id"], status="published")
    options = request_options(offering)
    if not options.get(f'{data["kind"]}_enabled'):
        raise serializers.ValidationError("This product does not currently allow that request type.")
    variant = get_object_or_404(OfferingVariant, offering=offering, public_id=data["variant_public_id"], is_active=True)
    location = get_object_or_404(BusinessLocation, business=business, public_id=data["location_public_id"], is_active=True)
    if ProductRequest.objects.filter(business=business, email=data["email"], status__in=["pending", "held", "approved", "collected"]).count() >= 5:
        raise RequestConflict("You already have five active requests. Please contact the business to manage them.")
    item = ProductRequest(
        business=business, offering=offering, variant=variant, location=location,
        kind=data["kind"], quantity=data["quantity"], first_name=data["first_name"], last_name=data["last_name"],
        email=data["email"], phone=data["phone"], notes=data["notes"], starts_on=data.get("starts_on"), ends_on=data.get("ends_on"),
        idempotency_digest=key, payload_digest=digest,
        snapshot={"name": offering.name, "variant": variant.name, "sku": variant.sku, "currency": business.currency,
                  "purchase_unit_price": str(variant.price), "terms": options[f'{data["kind"]}_terms']},
    )
    if item.kind == "reservation":
        hold_request_stock(item)
        item.status = "held"
        item.expires_at = timezone.now() + timedelta(hours=options["hold_hours"])
    item.save()
    record_audit(business, None, "product_request.created", "product_request", item.public_id, {"kind": item.kind})
    return item, True


@transaction.atomic
def transition_product_request(business, public_id, action, actor, note="", ends_on=None, expected_updated_at=None):
    Business.objects.select_for_update().get(pk=business.pk)
    item = get_object_or_404(ProductRequest.objects.select_for_update(), business=business, public_id=public_id)
    if expected_updated_at and item.updated_at != expected_updated_at:
        raise RequestConflict('This request has changed. Refresh it before recording your action.')
    if action in {'extend', 'follow_up'}:
        if not note.strip():
            raise serializers.ValidationError({'note': 'Record the agreed arrangements or follow-up outcome.'})
        if action == 'extend':
            today = timezone.now().astimezone(ZoneInfo(business.timezone)).date()
            if item.kind != 'rental' or item.status not in {'approved', 'collected'}:
                raise RequestConflict('Only approved or collected rentals can be extended.')
            if not ends_on or ends_on <= item.ends_on or ends_on < today or (ends_on - today).days > 365:
                raise serializers.ValidationError({'ends_on': 'Choose a later return date, today or within the next 365 days.'})
            previous_end = str(item.ends_on)
            item.ends_on = ends_on
        item.decision_note = note
        item.save(update_fields=['decision_note', 'ends_on', 'updated_at'])
        metadata = {'note': note}
        if action == 'extend': metadata.update(previous_ends_on=previous_end, ends_on=str(ends_on))
        record_audit(business, actor, f'product_request.{action}', 'product_request', item.public_id, metadata)
        return item
    transitions = {
        "approve": ("pending", "approved"), "reject": ("pending", "rejected"),
        "collect": ("approved", "collected"), "return": ("collected", "returned"),
        "convert": ("held", "converted"),
    }
    if action == "cancel" and item.status in {"pending", "held", "approved"}:
        destination = "cancelled"
    elif action in transitions and item.status == transitions[action][0]:
        destination = transitions[action][1]
    else:
        raise RequestConflict("This request changed or that action is no longer available. Refresh and review its status.")
    if action in {"reject", "cancel"} and not note.strip():
        raise serializers.ValidationError({"note": "Include a reason for this decision."})
    if action == "approve":
        if item.offering.status != "published" or not item.offering.track_inventory or not item.variant.is_active or not item.location.is_active:
            raise RequestConflict("The product, variant, inventory tracking, or collection location is no longer active.")
        today = timezone.now().astimezone(ZoneInfo(business.timezone)).date()
        if item.ends_on < today:
            raise RequestConflict("This rental period has passed. Reject it and ask the customer for new dates.")
        hold_request_stock(item)
    elif action in {"cancel", "return", "convert"}:
        release_request_stock(item)
    if action == "convert":
        if item.expires_at <= timezone.now():
            raise RequestConflict("This stock reservation has expired.")
        if item.offering.status != "published" or not item.offering.track_inventory or not item.variant.is_active or not item.location.is_active:
            raise RequestConflict("The product, variant, or location is no longer active. Cancel this request instead.")
        cart, _ = create_cart(business)
        cart.location = item.location
        cart.save(update_fields=["location"])
        from .serializers import CartItemInputSerializer
        cart_input = CartItemInputSerializer(data={
            "offering_public_id": str(item.offering.public_id),
            "variant_public_id": str(item.variant.public_id), "quantity": item.quantity,
        }, context={"cart": cart})
        # Required modifiers must not be bypassed by the reservation conversion path.
        cart_input.is_valid(raise_exception=True)
        CartItem.objects.create(cart=cart, offering=item.offering, variant=item.variant, quantity=item.quantity,
                                unit_price=cart_input.validated_data["unit_price"], tax_rate=item.offering.tax_rate,
                                metadata={"note": f"Stock reservation {item.public_id}"})
        item.order = create_order_from_cart(cart, {"email": item.email, "first_name": item.first_name,
                                                  "last_name": item.last_name, "phone": item.phone,
                                                  "payment_method": "manual", "fulfillment_type": "pickup"})
    item.status = destination
    item.decision_note = note
    item.save()
    record_audit(business, actor, f"product_request.{action}", "product_request", item.public_id, {"status": destination, "note": note})
    return item
