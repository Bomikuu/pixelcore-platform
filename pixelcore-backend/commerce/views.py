import hashlib
import secrets
import uuid
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace

from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from businesses.api import BusinessScopedModelViewSet
from businesses.models import Business, DeviceLink
from businesses.services import device_from_token, record_audit
from businesses.views import member_business
from .models import Cart, CartItem, Customer, CustomerAddress, DigitalDownloadGrant, Discount, Fulfillment, Order, PaymentAttempt, PaymentConnection, PosSession, Refund, SavedOffering, ShippingZone
from .discounts import discount_amount, discount_states
from .live_sales import LivePagination, ORDER_SCOPES, order_counts
from .serializers import (
    CartItemInputSerializer, CartSerializer, CartUpdateSerializer, CheckoutSerializer, CustomerPortalAddressSerializer, CustomerPortalProfileSerializer, CustomerSerializer, OrderSerializer, PublicOrderConfirmationSerializer,
    DiscountSerializer, PaymentConnectionSerializer, SavedOfferingSerializer, ShippingZoneSerializer,
)
from .services import (
    PaymentProviderError, create_cart, create_order_from_cart, create_paymongo_checkout,
    active_discount, digital_delivery_tokens, process_paymongo_webhook, token_digest,
)
from scheduling.models import StaffProfile
from workforce.services import verify_staff_pin


POS_AUTHORIZATION_SALT = "pixelcore.pos-manager-authorization"
POS_AUTHORIZATION_MAX_AGE = 2 * 60


def pos_authorization_payload(request, device, session, action):
    token = request.headers.get("X-POS-Authorization", "")
    if not token:
        return None
    try:
        payload = signing.loads(token, salt=POS_AUTHORIZATION_SALT, max_age=POS_AUTHORIZATION_MAX_AGE)
    except signing.BadSignature:
        return None
    return payload if (
        payload.get("device") == str(device.public_id)
        and payload.get("version") == device.token_version
        and payload.get("revision") == session.revision
        and payload.get("action") == action
    ) else None


def pos_authorization_is_valid(request, device, session, action):
    return bool(pos_authorization_payload(request, device, session, action))


def strict_pos_response(action):
    labels = {"void_items": "A manager PIN is required to reduce items.", "void_sale": "A manager PIN is required to void this sale.", "discount": "A manager PIN is required to apply this discount.", "refund": "A manager PIN is required to record a refund."}
    return Response({"error": {"code": "POS_AUTHORIZATION_REQUIRED", "message": labels[action], "details": {"action": action}}}, status=403)


def build_pos_snapshot(business, payload):
    raw_items = payload.get("items") or []
    if not raw_items:
        return {"items": [], "currency": business.currency, "subtotal": "0.00", "tax_total": "0.00", "discount_total": "0.00", "grand_total": "0.00"}
    cart_context = SimpleNamespace(business=business)
    items = []
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for raw_item in raw_items:
        serializer = CartItemInputSerializer(data=raw_item, context={"cart": cart_context})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        line_total = data["unit_price"] * data["quantity"]
        image_asset = data["offering"].assets.filter(asset_type="image").first()
        subtotal += line_total
        rate = data["offering"].tax_rate / Decimal("100")
        if rate:
            tax_total += line_total - (line_total / (Decimal("1") + rate)) if business.prices_include_tax else line_total * rate
        items.append({
            "offering_public_id": str(data["offering"].public_id),
            "variant_public_id": str(data["variant"].public_id) if data["variant"] else None,
            "name": data["offering"].name,
            "variant_name": data["variant"].name if data["variant"] else "",
            "quantity": data["quantity"],
            "unit_price": str(data["unit_price"].quantize(Decimal("0.01"))),
            "line_total": str(line_total.quantize(Decimal("0.01"))),
            "image_url": image_asset.file.url if image_asset else "",
            "options": [{"public_id": str(option.public_id), "name": option.name, "price_delta": str(option.price_delta)} for option in data["options"]],
            "note": str(raw_item.get("note") or "").strip()[:300],
        })
    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax_total = tax_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    discount = active_discount(business, payload.get("discount_code", ""))
    if payload.get("discount_code") and not discount:
        raise ValidationError({"discount_code": "This promotion code is invalid or expired."})
    discount_total = discount_amount(discount, [(item["offering_public_id"], item["line_total"]) for item in items])
    grand_total = subtotal if business.prices_include_tax else subtotal + tax_total
    grand_total = max(Decimal("0"), grand_total - discount_total).quantize(Decimal("0.01"))
    return {"items": items, "currency": business.currency, "subtotal": str(subtotal), "tax_total": str(tax_total), "discount_total": str(discount_total), "grand_total": str(grand_total), "discount_code": payload.get("discount_code", "")}


def pos_session_payload(session):
    return {
        "public_id": str(session.public_id),
        "station_public_id": str(session.station.public_id),
        "station_name": session.station.name,
        "revision": session.revision,
        "cart": session.cart_snapshot or build_pos_snapshot(session.business, {}),
        "last_order": OrderSerializer(session.last_order).data if session.last_order_id else None,
        "held_sales": session.held_sales,
        "updated_at": session.updated_at,
    }


def pos_items_were_reduced(current_snapshot, incoming_snapshot):
    current = {}
    incoming = {}
    for item in (current_snapshot or {}).get("items", []):
        key = (str(item.get("offering_public_id") or ""), str(item.get("variant_public_id") or ""))
        current[key] = current.get(key, 0) + int(item.get("quantity") or 0)
    for item in (incoming_snapshot or {}).get("items", []):
        key = (str(item.get("offering_public_id") or ""), str(item.get("variant_public_id") or ""))
        incoming[key] = incoming.get(key, 0) + int(item.get("quantity") or 0)
    return any(incoming.get(key, 0) < quantity for key, quantity in current.items())


class CustomerViewSet(BusinessScopedModelViewSet):
    queryset = Customer.objects.prefetch_related("addresses")
    serializer_class = CustomerSerializer
    audit_resource = "customer"


class OrderViewSet(BusinessScopedModelViewSet):
    pagination_class = LivePagination
    queryset = Order.objects.prefetch_related("items", "fulfillments", "payment_attempts")
    serializer_class = OrderSerializer
    http_method_names = ["get", "patch", "head", "options"]
    audit_resource = "order"

    def get_queryset(self):
        queryset = super().get_queryset()
        scope = self.request.query_params.get('scope', 'all')
        if scope not in ORDER_SCOPES:
            raise ValidationError({'scope': 'Choose a supported order view.'})
        queryset = queryset.filter(ORDER_SCOPES[scope])
        search = self.request.query_params.get('search', '').strip()[:120]
        if search:
            queryset = queryset.filter(Q(number__icontains=search) | Q(customer_snapshot__email__icontains=search) | Q(customer_snapshot__first_name__icontains=search) | Q(customer_snapshot__last_name__icontains=search))
        for field in ("status", "payment_status", "fulfillment_type"):
            if self.request.query_params.get(field):
                queryset = queryset.filter(**{field: self.request.query_params[field]})
        return queryset

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['summary'] = order_counts(self.get_business())
        return response

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        previous_payment = serializer.instance.payment_status
        order = serializer.save()
        if previous_status != order.status:
            from operations.services import commit_order_stock, release_order_stock
            if order.status == "fulfilled":
                commit_order_stock(order, self.request.user)
            elif order.status == "cancelled":
                release_order_stock(order)
        if previous_payment != "paid" and order.payment_status == "paid" and digital_delivery_tokens(order):
            from .tasks import send_digital_delivery
            send_digital_delivery.delay(order.id)
        record_audit(order.business, self.request.user, "order.updated", "order", order.public_id)


class ShippingZoneViewSet(BusinessScopedModelViewSet):
    queryset = ShippingZone.objects.all()
    serializer_class = ShippingZoneSerializer
    audit_resource = "shipping_zone"


class DiscountViewSet(BusinessScopedModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    audit_resource = "discount"
    pagination_class = LivePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
        state = self.request.query_params.get("status", "")
        if state in discount_states():
            queryset = queryset.filter(discount_states()[state])
        scope = self.request.query_params.get("scope", "")
        if scope == "categories":
            queryset = queryset.exclude(category_ids=[])
        elif scope == "products":
            queryset = queryset.exclude(offering_ids=[])
        elif scope == "catalog":
            queryset = queryset.filter(offering_ids=[], category_ids=[])
        return queryset.order_by("-updated_at", "-pk")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        all_promotions = Discount.objects.filter(business=self.get_business())
        response.data["summary"] = {"total": all_promotions.count(), **{
            key: all_promotions.filter(condition).count() for key, condition in discount_states().items()
        }}
        return response



class PaymentConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        return Response(PaymentConnectionSerializer(business.payment_connections.all(), many=True).data)

    def put(self, request, public_id, provider):
        business = member_business(request.user, public_id, management=True)
        instance = PaymentConnection.objects.filter(business=business, provider=provider).first()
        serializer = PaymentConnectionSerializer(instance, data={**request.data, "provider": provider}, context={"business": business})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def authorized_cart(request, slug, cart_id):
    business = get_object_or_404(Business, slug=slug, status="active")
    cart = get_object_or_404(Cart.objects.select_related("business", "discount").prefetch_related("items__offering", "items__variant"), business=business, public_id=cart_id)
    supplied = request.headers.get("X-Cart-Token", "")
    if not secrets.compare_digest(cart.access_token_digest, token_digest(supplied)):
        return None, Response({"error": {"code": "CART_ACCESS_DENIED", "message": "This cart cannot be accessed.", "details": {}}}, status=403)
    return cart, None


class PublicCartCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        cart, token = create_cart(business)
        return Response({**CartSerializer(cart).data, "cart_token": token}, status=status.HTTP_201_CREATED)


class PublicCartDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, cart_id):
        cart, error = authorized_cart(request, slug, cart_id)
        return error or Response(CartSerializer(cart).data)

    def patch(self, request, slug, cart_id):
        cart, error = authorized_cart(request, slug, cart_id)
        if error:
            return error
        if cart.status != "open" or cart.expires_at <= timezone.now():
            return Response({"error": {"code": "CART_CLOSED", "message": "This cart is no longer open.", "details": {}}}, status=409)
        serializer = CartUpdateSerializer(data=request.data, context={"cart": cart})
        serializer.is_valid(raise_exception=True)
        if "discount_code" in serializer.validated_data:
            code = serializer.validated_data["discount_code"]
            cart.discount = active_discount(cart.business, code) if code else None
        if "fulfillment_type" in serializer.validated_data:
            cart.fulfillment_type = serializer.validated_data["fulfillment_type"]
        cart.save(update_fields=["discount", "fulfillment_type", "updated_at"])
        return Response(CartSerializer(cart).data)


class PublicCartItemView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, slug, cart_id):
        cart, error = authorized_cart(request, slug, cart_id)
        if error:
            return error
        if cart.status != "open" or cart.expires_at <= timezone.now():
            return Response({"error": {"code": "CART_CLOSED", "message": "This cart is no longer open.", "details": {}}}, status=409)
        serializer = CartItemInputSerializer(data=request.data, context={"cart": cart})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        offering, variant = data["offering"], data["variant"]
        options = data["options"]
        option_snapshot = [
            {
                "public_id": str(option.public_id),
                "group": option.group.name,
                "name": option.name,
                "price_delta": str(option.price_delta),
                "cost_delta": str(option.cost_delta),
            }
            for option in options
        ]
        metadata = {**data.get("metadata", {}), "options": option_snapshot}
        selection_key = hashlib.sha256("|".join(sorted(str(option.public_id) for option in options)).encode()).hexdigest()
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            offering=offering,
            variant=variant,
            selection_key=selection_key,
            defaults={"quantity": data["quantity"], "unit_price": data["unit_price"], "tax_rate": offering.tax_rate, "metadata": metadata},
        )
        if not created:
            item.quantity = data["quantity"]
            item.unit_price = data["unit_price"]
            item.metadata = metadata
            item.save(update_fields=["quantity", "unit_price", "metadata"])
        cart.save(update_fields=["updated_at"])
        cart._prefetched_objects_cache.pop("items", None)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, slug, cart_id, item_id):
        cart, error = authorized_cart(request, slug, cart_id)
        if error:
            return error
        get_object_or_404(CartItem, cart=cart, public_id=item_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def patch(self, request, slug, cart_id, item_id):
        cart, error = authorized_cart(request, slug, cart_id)
        if error:
            return error
        if cart.status != "open" or cart.expires_at <= timezone.now():
            return Response({"error": {"code": "CART_CLOSED", "message": "This cart is no longer open.", "details": {}}}, status=409)
        item = get_object_or_404(CartItem.objects.select_for_update().select_related("offering"), cart=cart, public_id=item_id)
        current_options = [option.get("public_id") for option in item.metadata.get("options", []) if option.get("public_id")]
        payload = {
            "offering_public_id": str(item.offering.public_id),
            "variant_public_id": request.data.get("variant_public_id", str(item.variant.public_id) if item.variant_id else None),
            "quantity": request.data.get("quantity", item.quantity),
            "option_public_ids": request.data.get("option_public_ids", current_options),
            "metadata": {**item.metadata, **(request.data.get("metadata") or {})},
        }
        serializer = CartItemInputSerializer(data=payload, context={"cart": cart})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        options = data["options"]
        selection_key = hashlib.sha256("|".join(sorted(str(option.public_id) for option in options)).encode()).hexdigest()
        duplicate = CartItem.objects.filter(cart=cart, offering=item.offering, variant=data["variant"], selection_key=selection_key).exclude(pk=item.pk).first()
        if duplicate:
            duplicate.quantity += data["quantity"]
            duplicate.unit_price = data["unit_price"]
            duplicate.save(update_fields=["quantity", "unit_price"])
            item.delete()
        else:
            item.variant = data["variant"]
            item.quantity = data["quantity"]
            item.unit_price = data["unit_price"]
            item.selection_key = selection_key
            item.metadata = {**data.get("metadata", {}), "options": [{"public_id": str(option.public_id), "group": option.group.name, "name": option.name, "price_delta": str(option.price_delta), "cost_delta": str(option.cost_delta)} for option in options]}
            item.save(update_fields=["variant", "quantity", "unit_price", "selection_key", "metadata"])
        cart.save(update_fields=["updated_at"])
        cart._prefetched_objects_cache.pop("items", None)
        return Response(CartSerializer(cart).data)


class PublicCheckoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, slug, cart_id):
        cart, error = authorized_cart(request, slug, cart_id)
        if error:
            return error
        serializer = CheckoutSerializer(data=request.data, context={"business": cart.business})
        serializer.is_valid(raise_exception=True)
        try:
            order = create_order_from_cart(cart, serializer.validated_data)
        except ValueError as exc:
            return Response({"error": {"code": "CHECKOUT_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        payload = OrderSerializer(order).data
        if order.payment_method == "paymongo":
            try:
                attempt = create_paymongo_checkout(
                    order,
                    serializer.validated_data.get("success_url", ""),
                    serializer.validated_data.get("cancel_url", ""),
                    request.headers.get("Idempotency-Key") or secrets.token_urlsafe(24),
                )
                payload["checkout_url"] = attempt.checkout_url
            except PaymentProviderError as exc:
                return Response({"error": {"code": "PAYMENT_PROVIDER_ERROR", "message": str(exc), "details": {"order": order.number}}}, status=502)
        return Response(payload, status=status.HTTP_201_CREATED)


class PayMongoWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, business_id):
        business = get_object_or_404(Business, public_id=business_id, status="active")
        try:
            process_paymongo_webhook(business, request.body, request.headers.get("Paymongo-Signature", ""))
        except (PaymentProviderError, PaymentConnection.DoesNotExist):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicShippingZoneListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        return Response(ShippingZoneSerializer(business.shipping_zones.filter(is_active=True), many=True).data)


class PublicDigitalDownloadView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def get(self, request):
        try:
            payload = signing.loads(request.query_params.get("token", ""), salt="pixelcore-digital-download", max_age=7 * 24 * 60 * 60)
        except signing.BadSignature:
            return Response({"error": {"code": "INVALID_DOWNLOAD", "message": "This download link is invalid or expired.", "details": {}}}, status=404)
        grant = get_object_or_404(
            DigitalDownloadGrant.objects.select_for_update().select_related("order_item__order", "order_item__offering__digital_asset"),
            public_id=payload.get("grant"),
        )
        asset = grant.order_item.offering.digital_asset
        if grant.expires_at <= timezone.now() or grant.download_count >= grant.max_downloads or grant.order_item.order.payment_status != "paid" or not asset:
            return Response({"error": {"code": "DOWNLOAD_UNAVAILABLE", "message": "This download is no longer available.", "details": {}}}, status=410)
        grant.download_count += 1
        grant.save(update_fields=["download_count"])
        return FileResponse(asset.file.open("rb"), as_attachment=True, filename=asset.file.name.rsplit("/", 1)[-1])


def customer_for_account(user, business):
    customer = Customer.objects.filter(business=business, user=user).first()
    if customer:
        return customer
    customer = Customer.objects.filter(business=business, email__iexact=user.email).first()
    if customer:
        customer.user = user
        customer.save(update_fields=["user", "updated_at"])
    return customer


class CustomerPortalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if not customer:
            return Response({"customer": None, "saved": [], "orders": [], "bookings": []})
        bookings = customer.bookings.select_related("offering", "staff").prefetch_related("resources")
        from scheduling.serializers import BookingSerializer
        return Response({
            "customer": CustomerSerializer(customer).data,
            "saved": SavedOfferingSerializer(customer.saved_offerings.select_related("offering"), many=True).data,
            "orders": OrderSerializer(customer.orders.prefetch_related("items", "fulfillments", "payment_attempts"), many=True).data,
            "bookings": BookingSerializer(bookings, many=True).data,
        })

    @transaction.atomic
    def patch(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if not customer:
            customer = Customer.objects.create(
                business=business,
                user=request.user,
                email=request.user.email,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
            )
        serializer = CustomerPortalProfileSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CustomerSerializer(customer).data)


class CustomerPortalAddressView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if not customer:
            customer = Customer.objects.create(
                business=business,
                user=request.user,
                email=request.user.email,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
            )
        serializer = CustomerPortalAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        addresses = list(customer.addresses.select_for_update())
        make_default = serializer.validated_data.get("is_default", False) or not addresses
        if make_default:
            customer.addresses.update(is_default=False)
        address = serializer.save(customer=customer, is_default=make_default)
        return Response(CustomerPortalAddressSerializer(address).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request, slug, address_id):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if not customer:
            raise Http404
        list(customer.addresses.select_for_update())
        address = get_object_or_404(
            CustomerAddress,
            customer=customer,
            public_id=address_id,
        )
        was_default = address.is_default
        serializer = CustomerPortalAddressSerializer(address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("is_default"):
            customer.addresses.exclude(pk=address.pk).update(is_default=False)
        address = serializer.save()
        if was_default and not address.is_default:
            next_address = customer.addresses.exclude(pk=address.pk).order_by("id").first()
            if next_address:
                next_address.is_default = True
                next_address.save(update_fields=["is_default"])
            else:
                address.is_default = True
                address.save(update_fields=["is_default"])
        return Response(CustomerPortalAddressSerializer(address).data)

    @transaction.atomic
    def delete(self, request, slug, address_id):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if not customer:
            raise Http404
        list(customer.addresses.select_for_update())
        address = get_object_or_404(
            CustomerAddress,
            customer=customer,
            public_id=address_id,
        )
        was_default = address.is_default
        address.delete()
        if was_default:
            next_address = customer.addresses.order_by("id").first()
            if next_address:
                next_address.is_default = True
                next_address.save(update_fields=["is_default"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerSavedOfferingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if not customer:
            customer = Customer.objects.create(
                business=business,
                user=request.user,
                email=request.user.email,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
            )
        serializer = SavedOfferingSerializer(data=request.data, context={"business": business})
        serializer.is_valid(raise_exception=True)
        saved, created = SavedOffering.objects.get_or_create(customer=customer, offering=serializer.validated_data["offering"], defaults={"business": business})
        return Response(SavedOfferingSerializer(saved).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, slug, offering_id):
        business = get_object_or_404(Business, slug=slug, status="active")
        customer = customer_for_account(request.user, business)
        if customer:
            SavedOffering.objects.filter(customer=customer, offering__public_id=offering_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerSavedOfferingMergeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        raw_ids = request.data.get("offering_public_ids") or []
        if not isinstance(raw_ids, list) or len(raw_ids) > 100:
            raise ValidationError({"offering_public_ids": "Send no more than 100 product identifiers."})
        requested_ids = {str(value) for value in raw_ids}
        offerings = list(business.offerings.filter(public_id__in=requested_ids, status="published").exclude(offering_type="service"))
        if len(offerings) != len(requested_ids):
            raise ValidationError({"offering_public_ids": "One or more products are unavailable."})
        customer = customer_for_account(request.user, business)
        if not customer:
            customer = Customer.objects.create(business=business, user=request.user, email=request.user.email, first_name=request.user.first_name, last_name=request.user.last_name)
        for offering in offerings:
            SavedOffering.objects.get_or_create(business=business, customer=customer, offering=offering)
        return Response(SavedOfferingSerializer(customer.saved_offerings.select_related("offering"), many=True, context={"business": business}).data)


class PublicOrderConfirmationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, order_id):
        business = get_object_or_404(Business, slug=slug, status="active")
        order = get_object_or_404(Order.objects.select_related("cart").prefetch_related("items", "fulfillments", "payment_attempts"), business=business, public_id=order_id)
        supplied = request.headers.get("X-Cart-Token", "")
        if not order.cart_id or not secrets.compare_digest(order.cart.access_token_digest, token_digest(supplied)):
            return Response({"error": {"code": "ORDER_ACCESS_DENIED", "message": "This order confirmation cannot be accessed.", "details": {}}}, status=403)
        return Response(PublicOrderConfirmationSerializer(order).data)


@transaction.atomic
def complete_pos_checkout(business, payload, actor=None, source_device=None, idempotency_key=""):
    items = payload.get("items") or []
    if not items:
        raise ValidationError({"items": "Add at least one item."})
    cart, _ = create_cart(business)
    for item_payload in items:
        serializer = CartItemInputSerializer(data=item_payload, context={"cart": cart})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        options = data["options"]
        options_snapshot = [{"public_id": str(option.public_id), "group": option.group.name, "name": option.name, "price_delta": str(option.price_delta), "cost_delta": str(option.cost_delta)} for option in options]
        selection_key = hashlib.sha256("|".join(sorted(str(option.public_id) for option in options)).encode()).hexdigest()
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            offering=data["offering"],
            variant=data["variant"],
            selection_key=selection_key,
            defaults={"quantity": data["quantity"], "unit_price": data["unit_price"], "tax_rate": data["offering"].tax_rate, "metadata": {"options": options_snapshot, "note": str(item_payload.get("note") or "").strip()[:300]}},
        )
        if not created:
            item.quantity += data["quantity"]
            item.unit_price = data["unit_price"]
            item.metadata = {"options": options_snapshot, "note": str(item_payload.get("note") or "").strip()[:300]}
            item.save(update_fields=["quantity", "unit_price", "metadata"])
    customer = payload.get("customer") or {}
    shipping_address = payload.get("shipping_address") or {}
    if payload.get("fulfillment_type") == "delivery" and not all(shipping_address.get(field) for field in ("line1", "city", "region")):
        raise ValidationError({"shipping_address": "Street address, city, and region are required for delivery."})
    checkout_data = {
        "email": customer.get("email") or f"walk-in-{cart.public_id}@pos.pixelcore.local",
        "first_name": customer.get("first_name") or "Walk-in",
        "last_name": customer.get("last_name") or "customer",
        "phone": customer.get("phone", ""),
        "fulfillment_type": payload.get("fulfillment_type", "pickup"),
        "payment_method": payload.get("payment_method", "manual"),
        "discount_code": payload.get("discount_code", ""),
        "shipping_address": shipping_address,
    }
    if checkout_data["payment_method"] not in {"cash", "card", "gcash", "maya", "manual", "cod"}:
        raise ValidationError({"payment_method": "POS accepts configured in-person or cash payment methods."})
    order = create_order_from_cart(cart, checkout_data)
    order.source_device = source_device
    payment_status = payload.get("payment_status", "paid")
    if payment_status not in {"paid", "unpaid"}:
        raise ValidationError({"payment_status": "Choose paid or unpaid."})
    order.payment_status = payment_status
    order.status = "confirmed"
    order.notes = str(payload.get("order_note") or "").strip()[:2000]
    order.save(update_fields=["source_device", "payment_status", "status", "notes", "updated_at"])
    if payment_status == "paid":
        PaymentAttempt.objects.create(
            business=business,
            order=order,
            provider=f"pos_{checkout_data['payment_method']}",
            provider_reference=f"{source_device.public_id if source_device else 'workspace'}:{order.number}",
            status="paid",
            amount=order.grand_total,
            currency=order.currency,
            idempotency_key=(idempotency_key or f"pos-{order.public_id}")[:120],
            raw_status={"recorded_at_counter": True},
        )
    record_audit(business, actor, "pos.order.completed", "order", order.public_id)
    return order


class PosCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        order = complete_pos_checkout(business, request.data, request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class DevicePosCheckoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.select_for_update().get_or_create(business=device.business, station=device)
        checkout_key = str(request.headers.get("Idempotency-Key") or request.data.get("idempotency_key") or "")[:120]
        if checkout_key and session.last_checkout_key == checkout_key and session.last_order_id:
            return Response({**OrderSerializer(session.last_order).data, "pos_session": pos_session_payload(session)})
        expected = request.data.get("if_revision")
        if expected is not None:
            try:
                if int(expected) != session.revision:
                    return Response({"error": {"code": "POS_SESSION_CONFLICT", "message": "This sale changed before checkout. Review the latest server-priced cart.", "details": {"current_revision": session.revision}}, "session": pos_session_payload(session)}, status=409)
            except (TypeError, ValueError):
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "if_revision must be an integer.", "details": {}}}, status=400)
        requested_method = str(request.data.get("payment_method") or "manual")
        configured_methods = set(device.configuration.get("payment_methods", ["cash", "card", "gcash", "maya", "pay_later", "manual"]))
        configured_method = "pay_later" if requested_method == "cod" else requested_method
        if configured_method not in configured_methods:
            return Response({"error": {"code": "PAYMENT_METHOD_DISABLED", "message": "This payment method is not enabled for the counter.", "details": {"payment_method": configured_method}}}, status=409)
        order = complete_pos_checkout(device.business, request.data, source_device=device, idempotency_key=checkout_key)
        session.cart_snapshot = build_pos_snapshot(device.business, {})
        session.last_order = order
        session.last_checkout_key = checkout_key
        session.revision += 1
        session.save(update_fields=["cart_snapshot", "last_order", "last_checkout_key", "revision", "updated_at"])
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        return Response({**OrderSerializer(order).data, "pos_session": pos_session_payload(session)}, status=status.HTTP_201_CREATED)


class DevicePosSessionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_device(self, request):
        return device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])

    def get(self, request):
        device = self.get_device(request)
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.get_or_create(business=device.business, station=device)
        from catalog.serializers import OfferingSerializer
        offerings = device.business.offerings.filter(status="published").select_related("category").prefetch_related("variants", "assets", "option_groups__options", "cost_components")
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        business = device.business
        return Response({
            "business": {
                "display_name": business.display_name,
                "tagline": business.tagline,
                "currency": business.currency,
                "branding": business.branding,
                "logo_url": request.build_absolute_uri(business.logo.url) if business.logo else "",
            },
            "offerings": OfferingSerializer(offerings, many=True, context={"business": business, "request": request}).data,
            "session": pos_session_payload(session),
            "station_controls": {
                "strict_mode": bool(device.configuration.get("strict_mode", False)),
                "favorite_offering_ids": [str(value) for value in device.configuration.get("favorite_offering_ids", [])][:24],
                "payment_methods": [value for value in device.configuration.get("payment_methods", ["cash", "card", "gcash", "maya", "pay_later"]) if value in {"cash", "card", "gcash", "maya", "pay_later"}],
                "allow_delivery_payments": device.configuration.get("allow_delivery_payments", True) is not False,
                "receipt_options": [value for value in device.configuration.get("receipt_options", ["print", "digital"]) if value in {"print", "digital"}],
            },
            "discounts": [{"public_id": str(item.public_id), "name": item.name, "code": item.code, "value_type": item.value_type, "value": str(item.value)} for item in Discount.objects.filter(business=business, is_active=True).order_by("name")[:50]],
        })

    @transaction.atomic
    def put(self, request):
        device = self.get_device(request)
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.select_for_update().get_or_create(business=device.business, station=device)
        expected = request.data.get("if_revision")
        try:
            stale = expected is not None and int(expected) != session.revision
        except (TypeError, ValueError):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "if_revision must be an integer.", "details": {}}}, status=400)
        if stale:
            return Response({"error": {"code": "POS_SESSION_CONFLICT", "message": "This sale changed on another screen. Reload the current cart.", "details": {"current_revision": session.revision}}, "session": pos_session_payload(session)}, status=409)
        proposed_snapshot = build_pos_snapshot(device.business, request.data)
        if device.configuration.get("strict_mode"):
            if pos_items_were_reduced(session.cart_snapshot, proposed_snapshot) and not pos_authorization_is_valid(request, device, session, "void_items"):
                return strict_pos_response("void_items")
            current_discount = str((session.cart_snapshot or {}).get("discount_code") or "")
            incoming_discount = str(request.data.get("discount_code") or "")
            if incoming_discount and incoming_discount != current_discount and not pos_authorization_is_valid(request, device, session, "discount"):
                return strict_pos_response("discount")
        session.cart_snapshot = proposed_snapshot
        session.last_order = None
        session.revision += 1
        session.save(update_fields=["cart_snapshot", "last_order", "revision", "updated_at"])
        return Response(pos_session_payload(session))


class DevicePosAuthorizationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        action = str(request.data.get("action") or "")
        if action not in {"void_items", "void_sale", "discount", "refund"}:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose a supported register action.", "details": {"action": action}}}, status=400)
        pin = str(request.data.get("pin") or "")
        if len(pin) != 6 or not pin.isdigit():
            return Response({"error": {"code": "POS_AUTHORIZATION_DENIED", "message": "The manager PIN is incorrect or is not authorized for this business.", "details": {}}}, status=403)
        approvers = StaffProfile.objects.filter(
            business=device.business,
            employment_status="active",
            membership__status="active",
            membership__role__in=("owner", "admin", "manager"),
        ).select_related("membership__user")
        staff = next((candidate for candidate in approvers if verify_staff_pin(candidate, pin)), None)
        if not staff:
            return Response({"error": {"code": "POS_AUTHORIZATION_DENIED", "message": "The manager PIN is incorrect or is not authorized for this business.", "details": {}}}, status=403)
        session, _ = PosSession.objects.get_or_create(business=device.business, station=device)
        token = signing.dumps({"device": str(device.public_id), "version": device.token_version, "revision": session.revision, "action": action, "staff": str(staff.public_id)}, salt=POS_AUTHORIZATION_SALT, compress=True)
        record_audit(device.business, staff.membership.user, "pos.authorization.approved", "pos_session", session.public_id, {"action": action, "device": str(device.public_id)})
        return Response({"authorization_token": token, "approved_by": staff.display_name, "action": action, "expires_in_seconds": POS_AUTHORIZATION_MAX_AGE})


class DevicePosHoldView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_device(self, request):
        return device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])

    def get(self, request):
        device = self.get_device(request)
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.get_or_create(business=device.business, station=device)
        return Response({"held_sales": session.held_sales, "revision": session.revision})

    @transaction.atomic
    def post(self, request):
        device = self.get_device(request)
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.select_for_update().get_or_create(business=device.business, station=device)
        if not (session.cart_snapshot or {}).get("items"):
            return Response({"error": {"code": "EMPTY_POS_SALE", "message": "Add an item before holding this sale.", "details": {}}}, status=409)
        if len(session.held_sales) >= 20:
            return Response({"error": {"code": "POS_HOLD_LIMIT", "message": "Resume or remove a held sale before holding another.", "details": {"limit": 20}}}, status=409)
        hold = {
            "public_id": str(uuid.uuid4()),
            "label": str(request.data.get("label") or f"Held sale {len(session.held_sales) + 1}").strip()[:80],
            "held_at": timezone.now().isoformat(),
            "cart": session.cart_snapshot,
        }
        session.held_sales = [*session.held_sales, hold]
        session.cart_snapshot = build_pos_snapshot(device.business, {})
        session.last_order = None
        session.revision += 1
        session.save(update_fields=["held_sales", "cart_snapshot", "last_order", "revision", "updated_at"])
        record_audit(device.business, None, "pos.sale.held", "pos_session", session.public_id, {"hold_id": hold["public_id"], "device": str(device.public_id)})
        return Response(pos_session_payload(session), status=201)


class DevicePosHoldResumeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request, hold_id):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.select_for_update().get_or_create(business=device.business, station=device)
        if (session.cart_snapshot or {}).get("items"):
            return Response({"error": {"code": "POS_SESSION_NOT_EMPTY", "message": "Hold or complete the current sale before resuming another.", "details": {}}}, status=409)
        hold = next((item for item in session.held_sales if item.get("public_id") == str(hold_id)), None)
        if not hold:
            return Response({"error": {"code": "NOT_FOUND", "message": "This held sale is no longer available.", "details": {}}}, status=404)
        session.held_sales = [item for item in session.held_sales if item.get("public_id") != str(hold_id)]
        session.cart_snapshot = hold.get("cart") or build_pos_snapshot(device.business, {})
        session.revision += 1
        session.save(update_fields=["held_sales", "cart_snapshot", "revision", "updated_at"])
        record_audit(device.business, None, "pos.sale.resumed", "pos_session", session.public_id, {"hold_id": str(hold_id), "device": str(device.public_id)})
        return Response(pos_session_payload(session))


class DevicePosVoidView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.select_for_update().get_or_create(business=device.business, station=device)
        reason = str(request.data.get("reason") or "").strip()
        if len(reason) < 3 or len(reason) > 300:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Provide a void reason between 3 and 300 characters.", "details": {}}}, status=400)
        authorization = pos_authorization_payload(request, device, session, "void_sale")
        if device.configuration.get("strict_mode") and not authorization:
            return strict_pos_response("void_sale")
        actor = None
        if authorization:
            staff = StaffProfile.objects.select_related("membership__user").filter(public_id=authorization.get("staff"), business=device.business).first()
            actor = staff.membership.user if staff else None
        item_count = sum(int(item.get("quantity") or 0) for item in (session.cart_snapshot or {}).get("items", []))
        session.cart_snapshot = build_pos_snapshot(device.business, {})
        session.last_order = None
        session.revision += 1
        session.save(update_fields=["cart_snapshot", "last_order", "revision", "updated_at"])
        record_audit(device.business, actor, "pos.sale.voided", "pos_session", session.public_id, {"reason": reason, "item_count": item_count, "device": str(device.public_id)})
        return Response(pos_session_payload(session))


class DevicePosTransactionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        orders = Order.objects.filter(business=device.business, source_device=device).prefetch_related("items", "fulfillments", "payment_attempts").order_by("-placed_at")[:30]
        return Response({"orders": OrderSerializer(orders, many=True).data})


class DevicePosReceiptView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, order_id):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        order = Order.objects.filter(public_id=order_id, business=device.business, source_device=device).first()
        if not order:
            return Response({"error": {"code": "NOT_FOUND", "message": "This transaction is not available at this station.", "details": {}}}, status=404)
        email = str(request.data.get("email") or "").strip().lower()
        try:
            validate_email(email)
        except DjangoValidationError:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Enter a valid receipt email address.", "details": {}}}, status=400)
        from .tasks import send_pos_receipt
        send_pos_receipt.delay(order.id, email)
        record_audit(device.business, None, "pos.receipt.emailed", "order", order.public_id, {"device": str(device.public_id)})
        return Response({"queued": True, "email": email})


class DevicePosRefundView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request, order_id):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        session, _ = PosSession.objects.get_or_create(business=device.business, station=device)
        authorization = pos_authorization_payload(request, device, session, "refund")
        if not authorization:
            return strict_pos_response("refund")
        order = Order.objects.select_for_update().filter(public_id=order_id, business=device.business, source_device=device).first()
        if not order:
            return Response({"error": {"code": "NOT_FOUND", "message": "This transaction is not available at this station.", "details": {}}}, status=404)
        if order.payment_status != "paid":
            return Response({"error": {"code": "REFUND_CONFLICT", "message": "Only a paid transaction can be refunded.", "details": {"payment_status": order.payment_status}}}, status=409)
        reason = str(request.data.get("reason") or "").strip()
        if len(reason) < 3 or len(reason) > 300:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Provide a refund reason between 3 and 300 characters.", "details": {}}}, status=400)
        payment = order.payment_attempts.filter(status="paid").first()
        if not payment:
            return Response({"error": {"code": "REFUND_CONFLICT", "message": "This transaction has no recorded payment to refund.", "details": {}}}, status=409)
        staff = StaffProfile.objects.select_related("membership__user").filter(public_id=authorization.get("staff"), business=device.business).first()
        if not staff:
            return strict_pos_response("refund")
        Refund.objects.create(payment_attempt=payment, amount=order.grand_total, reason=reason, status="recorded", created_by=staff.membership.user)
        order.payment_status = "refunded"
        order.status = "refunded"
        order.save(update_fields=["payment_status", "status", "updated_at"])
        record_audit(device.business, staff.membership.user, "pos.order.refunded", "order", order.public_id, {"reason": reason, "device": str(device.public_id), "provider": payment.provider})
        return Response(OrderSerializer(order).data)


class PublicCustomerDisplayView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["customer_display"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This display is not paired.", "details": {}}}, status=403)
        link = DeviceLink.objects.filter(business=device.business, target_device=device, link_type="customer_display", is_active=True, source_device__is_active=True).select_related("source_device").first()
        session = PosSession.objects.select_related("station", "last_order").prefetch_related("last_order__items", "last_order__fulfillments", "last_order__payment_attempts").filter(station=link.source_device).first() if link else None
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        business = device.business
        configured_ids = [str(value) for value in device.configuration.get("promotion_display_ids", [])]
        content_mode = device.configuration.get("ad_content_mode", "all")
        publications = business.display_publications.filter(
            is_active=True,
            is_published=True,
            kind__in=("promotion", "information"),
        ).select_related("background_asset")
        if content_mode == "selected":
            publications = publications.filter(public_id__in=configured_ids) if configured_ids else publications.none()
        advertisements = []
        for publication in publications[:8]:
            settings = publication.settings if isinstance(publication.settings, dict) else {}
            advertisements.append({
                "public_id": str(publication.public_id),
                "name": publication.name,
                "heading": str(settings.get("heading") or publication.name)[:180],
                "message": str(settings.get("message") or "")[:300],
                "background": settings.get("background", "#102a2a"),
                "foreground": settings.get("foreground", "#f7f3ea"),
                "image_url": request.build_absolute_uri(publication.background_asset.file.url) if publication.background_asset else "",
            })
        try:
            rotation_seconds = int(device.configuration.get("ad_rotation_seconds", 10))
        except (TypeError, ValueError):
            rotation_seconds = 10
        return Response({
            "business": {
                "display_name": business.display_name,
                "tagline": business.tagline,
                "branding": business.branding,
                "currency": business.currency,
                "logo_url": request.build_absolute_uri(business.logo.url) if business.logo else "",
                "cover_image_url": request.build_absolute_uri(business.cover_image.url) if business.cover_image else "",
            },
            "linked": bool(link),
            "station_name": link.source_device.name if link else "",
            "session": pos_session_payload(session) if session else None,
            "advertisements": advertisements,
            "display_preferences": {
                "rotation_seconds": max(5, min(rotation_seconds, 30)),
                "show_brand_fallback": bool(device.configuration.get("show_brand_fallback", True)),
            },
        })


class DeviceOrderQueueView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos", "kitchen_display", "dispatch_display"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This order screen is not paired.", "details": {}}}, status=403)
        orders = Order.objects.filter(
            business=device.business,
            status__in=("confirmed", "processing"),
        ).select_related("customer", "cart").prefetch_related("items__offering__assets", "fulfillments", "payment_attempts")
        if device.device_type in {"pos", "dispatch_display"}:
            orders = orders.filter(fulfillment_type="delivery")
        else:
            orders = orders.exclude(fulfillment_type__in=("digital", "booking"))
            orders = orders.exclude(fulfillment_type="delivery", fulfillments__status="ready")
        if device.location_id:
            orders = orders.filter(Q(cart__location=device.location) | Q(cart__location__isnull=True))
        orders = orders.order_by("placed_at", "id")[:100]
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        return Response({
            "business": {
                "display_name": device.business.display_name,
                "currency": device.business.currency,
                "branding": device.business.branding,
                "logo_url": request.build_absolute_uri(device.business.logo.url) if device.business.logo else "",
            },
            "device": {"public_id": str(device.public_id), "name": device.name, "device_type": device.device_type},
            "queue_type": "delivery_overview" if device.device_type == "pos" else "delivery" if device.device_type == "dispatch_display" else "preparation",
            "orders": OrderSerializer(orders, many=True).data,
            "refreshed_at": timezone.now(),
        })


class DeviceOrderStatusView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def patch(self, request, order_id):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["kitchen_display", "dispatch_display"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This order screen is not paired.", "details": {}}}, status=403)
        order = Order.objects.select_for_update().filter(public_id=order_id, business=device.business).first()
        if not order:
            return Response({"error": {"code": "NOT_FOUND", "message": "This order is no longer available.", "details": {}}}, status=404)
        if device.device_type == "dispatch_display" and order.fulfillment_type != "delivery":
            return Response({"error": {"code": "ORDER_NOT_AVAILABLE", "message": "This order does not belong on the delivery queue.", "details": {}}}, status=409)
        if device.device_type == "kitchen_display" and order.fulfillment_type in {"digital", "booking"}:
            return Response({"error": {"code": "ORDER_NOT_AVAILABLE", "message": "This order does not require preparation.", "details": {}}}, status=409)
        if order.status not in {"confirmed", "processing"}:
            return Response({"error": {"code": "ORDER_STATUS_CONFLICT", "message": "This order was already completed or cancelled.", "details": {"status": order.status}}}, status=409)

        fulfillment = Fulfillment.objects.select_for_update().filter(order=order).first()
        if not fulfillment:
            fulfillment = Fulfillment.objects.create(order=order, fulfillment_type=order.fulfillment_type or "none")
        action = request.data.get("action")
        if action == "start":
            order.status = "processing"
        elif action == "ready":
            order.status = "processing"
            fulfillment.status = "ready"
            fulfillment.save(update_fields=["status"])
        elif action == "complete":
            if device.device_type == "kitchen_display" and order.fulfillment_type == "delivery":
                return Response({"error": {"code": "ORDER_STATUS_CONFLICT", "message": "Delivery orders are completed from the delivery screen.", "details": {}}}, status=409)
            if fulfillment.status != "ready":
                return Response({"error": {"code": "ORDER_STATUS_CONFLICT", "message": "Mark this order ready before completing it.", "details": {"fulfillment_status": fulfillment.status}}}, status=409)
            order.status = "fulfilled"
            fulfillment.status = "fulfilled"
            fulfillment.fulfilled_at = timezone.now()
            fulfillment.save(update_fields=["status", "fulfilled_at"])
            from operations.services import commit_order_stock
            try:
                commit_order_stock(order)
            except ValueError as exc:
                raise ValidationError({"inventory": str(exc)}) from exc
        else:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose start, ready, or complete.", "details": {"action": action}}}, status=400)

        order.save(update_fields=["status", "updated_at"])
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        record_audit(device.business, None, f"device_order.{action}", "order", order.public_id, {"device": str(device.public_id)})
        return Response(OrderSerializer(order).data)


class DeviceOrderPaymentView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request, order_id):
        device = device_from_token(request.headers.get("X-Device-Token", ""), ["pos"])
        if not device:
            return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "This POS station is not paired.", "details": {}}}, status=403)
        if device.configuration.get("allow_delivery_payments", True) is False:
            return Response({"error": {"code": "DEVICE_ACTION_DISABLED", "message": "Delivery payments are disabled for this counter.", "details": {}}}, status=403)
        order = Order.objects.select_for_update().filter(public_id=order_id, business=device.business, fulfillment_type="delivery").first()
        if not order:
            return Response({"error": {"code": "NOT_FOUND", "message": "This delivery order is no longer available.", "details": {}}}, status=404)
        if device.location_id and order.cart_id and order.cart.location_id and order.cart.location_id != device.location_id:
            return Response({"error": {"code": "NOT_FOUND", "message": "This delivery order is no longer available.", "details": {}}}, status=404)
        if order.status not in {"confirmed", "processing"}:
            return Response({"error": {"code": "ORDER_STATUS_CONFLICT", "message": "Payment cannot be collected for this order state.", "details": {"status": order.status}}}, status=409)
        if order.payment_status == "paid":
            return Response(OrderSerializer(order).data)
        payment_method = str(request.data.get("payment_method") or "")
        if payment_method not in {"cash", "card", "gcash", "maya", "manual"}:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose cash, card terminal, GCash, Maya, or manual payment.", "details": {"payment_method": payment_method}}}, status=400)
        idempotency_key = str(request.headers.get("Idempotency-Key") or request.data.get("idempotency_key") or "")[:120]
        if not idempotency_key:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "A payment idempotency key is required.", "details": {}}}, status=400)
        existing = PaymentAttempt.objects.filter(business=device.business, idempotency_key=idempotency_key).first()
        if existing and existing.order_id != order.id:
            return Response({"error": {"code": "PAYMENT_CONFLICT", "message": "This payment reference was already used for another order.", "details": {}}}, status=409)
        attempt, created = PaymentAttempt.objects.get_or_create(
            business=device.business,
            idempotency_key=idempotency_key,
            defaults={"order": order, "provider": f"pos_{payment_method}", "status": "paid", "amount": order.grand_total, "currency": order.currency, "raw_status": {"device": str(device.public_id), "payment_method": payment_method}},
        )
        if not created and attempt.status != "paid":
            return Response({"error": {"code": "PAYMENT_CONFLICT", "message": "This payment reference has not completed.", "details": {"status": attempt.status}}}, status=409)
        order.payment_method = payment_method
        order.payment_status = "paid"
        order.save(update_fields=["payment_method", "payment_status", "updated_at"])
        record_audit(device.business, None, "pos.delivery_payment.collected", "order", order.public_id, {"device": str(device.public_id), "payment_method": payment_method})
        return Response(OrderSerializer(order).data)
