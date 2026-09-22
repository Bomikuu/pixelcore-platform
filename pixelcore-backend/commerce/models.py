import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from businesses.models import Business, BusinessDevice, BusinessLocation
from catalog.models import Offering, OfferingVariant


class ProductRequestSettings(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="product_request_settings")
    reservation_enabled = models.BooleanField(default=False)
    rental_enabled = models.BooleanField(default=False)
    hold_hours = models.PositiveSmallIntegerField(default=24)


class ProductRequest(models.Model):
    """Physical stock holds and staff-reviewed rentals, separate from service bookings."""
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="product_requests")
    offering = models.ForeignKey(Offering, on_delete=models.PROTECT, related_name="product_requests")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.PROTECT, related_name="product_requests")
    location = models.ForeignKey(BusinessLocation, on_delete=models.PROTECT, related_name="product_requests")
    balance = models.ForeignKey("operations.InventoryBalance", on_delete=models.PROTECT, null=True, blank=True, related_name="product_requests")
    order = models.OneToOneField("Order", on_delete=models.PROTECT, null=True, blank=True, related_name="product_request")
    kind = models.CharField(max_length=16, choices=[("reservation", "Stock reservation"), ("rental", "Rental request")])
    status = models.CharField(max_length=16, default="pending", choices=[
        ("pending", "Awaiting approval"), ("held", "Stock held"), ("approved", "Rental approved"),
        ("collected", "Rental collected"), ("returned", "Returned"), ("converted", "Order created"),
        ("cancelled", "Cancelled"), ("rejected", "Rejected"), ("expired", "Expired"),
    ])
    quantity = models.PositiveSmallIntegerField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    notes = models.TextField(blank=True, max_length=1000)
    decision_note = models.CharField(max_length=500, blank=True)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    stock_held = models.BooleanField(default=False)
    snapshot = models.JSONField(default=dict)
    idempotency_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["business", "idempotency_digest"], name="unique_product_request_key")]
        indexes = [models.Index(fields=["business", "status"], name="product_request_status_idx")]


class Customer(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="customers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="business_customer_profiles")
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True, max_length=2000)
    accepts_marketing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business", "email"], condition=~Q(email=""), name="unique_business_customer_email")
        ]
        ordering = ["last_name", "first_name", "id"]


class CustomerAddress(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=80, blank=True)
    recipient_name = models.CharField(max_length=180)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=24, blank=True)
    country = models.CharField(max_length=2, default="PH")
    phone = models.CharField(max_length=32, blank=True)
    is_default = models.BooleanField(default=False)


class ShippingZone(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="shipping_zones")
    name = models.CharField(max_length=120)
    regions = models.JSONField(default=list)
    flat_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)


class Discount(models.Model):
    TYPE_CHOICES = [("percentage", "Percentage"), ("fixed", "Fixed amount")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="discounts")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, blank=True)
    value_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    is_automatic = models.BooleanField(default=False)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    offering_ids = models.JSONField(default=list, blank=True)
    category_ids = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "code"], condition=~Q(code=""), name="unique_business_discount_code")]
        ordering = ["name"]


class SavedOffering(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="saved_offerings")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="saved_offerings")
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="saved_by_customers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["customer", "offering"], name="unique_customer_saved_offering")]
        ordering = ["-created_at"]


class Cart(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("converted", "Converted"), ("expired", "Expired"), ("abandoned", "Abandoned")]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="carts")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, related_name="carts")
    access_token_digest = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    currency = models.CharField(max_length=3)
    fulfillment_type = models.CharField(max_length=16, blank=True)
    location = models.ForeignKey(BusinessLocation, on_delete=models.SET_NULL, blank=True, null=True, related_name="carts")
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, blank=True, null=True, related_name="carts")
    email = models.EmailField(blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class CartItem(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    offering = models.ForeignKey(Offering, on_delete=models.PROTECT, related_name="cart_items")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.PROTECT, blank=True, null=True, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    metadata = models.JSONField(default=dict, blank=True)
    selection_key = models.CharField(max_length=64, default="")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "offering", "variant", "selection_key"], name="unique_cart_offering_selection", nulls_distinct=False)]


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"), ("confirmed", "Confirmed"), ("processing", "Processing"),
        ("fulfilled", "Fulfilled"), ("cancelled", "Cancelled"), ("refunded", "Refunded"),
    ]
    PAYMENT_CHOICES = [("unpaid", "Unpaid"), ("pending", "Pending"), ("paid", "Paid"), ("partially_refunded", "Partially refunded"), ("refunded", "Refunded")]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="orders")
    source_device = models.ForeignKey("businesses.BusinessDevice", on_delete=models.SET_NULL, blank=True, null=True, related_name="orders")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, related_name="orders")
    cart = models.OneToOneField(Cart, on_delete=models.SET_NULL, blank=True, null=True, related_name="order")
    number = models.CharField(max_length=40)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default="pending")
    payment_status = models.CharField(max_length=24, choices=PAYMENT_CHOICES, default="unpaid")
    payment_method = models.CharField(max_length=32, blank=True)
    fulfillment_type = models.CharField(max_length=16, blank=True)
    currency = models.CharField(max_length=3)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2)
    customer_snapshot = models.JSONField(default=dict)
    shipping_snapshot = models.JSONField(default=dict)
    notes = models.TextField(blank=True, max_length=2000)
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "number"], name="unique_business_order_number")]
        ordering = ["-placed_at", "id"]


class OrderItem(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    offering = models.ForeignKey(Offering, on_delete=models.SET_NULL, blank=True, null=True, related_name="order_items")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.PROTECT, blank=True, null=True, related_name="order_items")
    name = models.CharField(max_length=180)
    sku = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    offering_snapshot = models.JSONField(default=dict)


class PosSession(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="pos_sessions")
    station = models.OneToOneField(BusinessDevice, on_delete=models.CASCADE, related_name="pos_session")
    cart_snapshot = models.JSONField(default=dict, blank=True)
    held_sales = models.JSONField(default=list, blank=True)
    revision = models.PositiveBigIntegerField(default=0)
    last_order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True, related_name="pos_sessions")
    last_checkout_key = models.CharField(max_length=120, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "id"]


class Fulfillment(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="fulfillments")
    fulfillment_type = models.CharField(max_length=16)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("ready", "Ready"), ("fulfilled", "Fulfilled"), ("cancelled", "Cancelled")], default="pending")
    tracking_reference = models.CharField(max_length=120, blank=True)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)


class PaymentConnection(models.Model):
    PROVIDERS = [("paymongo", "PayMongo"), ("stripe", "Stripe")]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="payment_connections")
    provider = models.CharField(max_length=24, choices=PROVIDERS)
    encrypted_secret_key = models.TextField(blank=True)
    encrypted_webhook_secret = models.TextField(blank=True)
    public_key = models.CharField(max_length=255, blank=True)
    is_live = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "provider"], name="unique_business_payment_provider")]


class PaymentAttempt(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="payment_attempts")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payment_attempts")
    provider = models.CharField(max_length=24)
    provider_reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=24, choices=[("created", "Created"), ("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed"), ("expired", "Expired")], default="created")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    checkout_url = models.URLField(blank=True)
    idempotency_key = models.CharField(max_length=120)
    raw_status = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "idempotency_key"], name="unique_business_payment_idempotency")]


class Refund(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment_attempt = models.ForeignKey(PaymentAttempt, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.CharField(max_length=300, blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default="pending")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_refunds")
    created_at = models.DateTimeField(auto_now_add=True)


class WebhookEvent(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="payment_webhooks")
    provider = models.CharField(max_length=24)
    event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "provider", "event_id"], name="unique_payment_webhook_event")]


class DigitalDownloadGrant(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="download_grant")
    expires_at = models.DateTimeField()
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
