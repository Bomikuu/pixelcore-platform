import uuid

from django.conf import settings
from django.db import models

from businesses.models import Business, BusinessAsset, BusinessLocation
from catalog.models import OfferingVariant
from commerce.models import Customer, Order, OrderItem, PaymentAttempt


class InventoryBalance(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="inventory_balances")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.PROTECT, related_name="inventory_balances")
    location = models.ForeignKey(BusinessLocation, on_delete=models.PROTECT, related_name="inventory_balances")
    on_hand = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reserved = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    low_stock_threshold = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    target_stock_level = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    bin_location = models.CharField(max_length=80, blank=True)
    preferred_supplier = models.ForeignKey(
        "Supplier",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="preferred_inventory_balances",
    )
    last_counted_at = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, max_length=1000)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["variant", "location"], name="unique_variant_location_balance")]
        ordering = ["variant__offering__name", "variant__name"]

    @property
    def available(self):
        return self.on_hand - self.reserved


class StockMovement(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="stock_movements")
    balance = models.ForeignKey(InventoryBalance, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=[
        ("receive", "Receive"), ("sale", "Sale"), ("return", "Return"), ("adjust", "Adjustment"),
        ("transfer_in", "Transfer in"), ("transfer_out", "Transfer out"),
    ])
    quantity_delta = models.DecimalField(max_digits=14, decimal_places=3)
    reference_type = models.CharField(max_length=40, blank=True)
    reference_id = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="stock_movements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class StockReservation(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="stock_reservations")
    balance = models.ForeignKey(InventoryBalance, on_delete=models.PROTECT, related_name="reservations")
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="stock_reservation")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    status = models.CharField(max_length=16, choices=[("active", "Active"), ("committed", "Committed"), ("released", "Released"), ("expired", "Expired")], default="active")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class Supplier(models.Model):
    CATEGORY_CHOICES = [
        ("manufacturer", "Manufacturer"),
        ("distributor", "Distributor"),
        ("wholesaler", "Wholesaler"),
        ("service_provider", "Service provider"),
        ("contractor", "Contractor"),
        ("marketplace", "Marketplace"),
        ("other", "Other"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=40, blank=True)
    category = models.CharField(max_length=24, choices=CATEGORY_CHOICES, default="distributor")
    image = models.ForeignKey(BusinessAsset, on_delete=models.SET_NULL, blank=True, null=True, related_name="supplier_images")
    contact_name = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True, max_length=1000)
    tax_id = models.CharField(max_length=64, blank=True)
    account_reference = models.CharField(max_length=80, blank=True)
    payment_terms_days = models.PositiveSmallIntegerField(default=0)
    lead_time_days = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True, max_length=2000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]


class SupplierProduct(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="supplier_products")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplied_products")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.PROTECT, related_name="supplier_sources")
    supplier_sku = models.CharField(max_length=100, blank=True)
    supplier_product_name = models.CharField(max_length=200, blank=True)
    last_unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    minimum_order_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=1)
    lead_time_days = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["supplier", "variant"], name="unique_supplier_variant_source")]
        ordering = ["variant__offering__name", "variant__name"]


class DocumentSequence(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="document_sequences")
    document_type = models.CharField(max_length=24)
    prefix = models.CharField(max_length=16)
    next_number = models.PositiveBigIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "document_type"], name="unique_business_document_sequence")]


class PurchaseOrder(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="purchase_orders")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    location = models.ForeignKey(BusinessLocation, on_delete=models.PROTECT, related_name="purchase_orders")
    number = models.CharField(max_length=40)
    status = models.CharField(max_length=24, choices=[("draft", "Draft"), ("ordered", "Ordered"), ("partially_received", "Partially received"), ("received", "Received"), ("cancelled", "Cancelled")], default="draft")
    ordered_at = models.DateField(blank=True, null=True)
    expected_at = models.DateField(blank=True, null=True)
    received_at = models.DateTimeField(blank=True, null=True)
    supplier_reference = models.CharField(max_length=120, blank=True)
    shipping_method = models.CharField(max_length=80, blank=True)
    shipping_address = models.TextField(blank=True, max_length=1000)
    notes = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "number"], name="unique_business_purchase_order_number")]
        ordering = ["-created_at"]


class PurchaseOrderLine(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.PROTECT, related_name="purchase_order_lines")
    description = models.CharField(max_length=200)
    quantity_ordered = models.DecimalField(max_digits=14, decimal_places=3)
    quantity_received = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)


class Quotation(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="quotations")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="quotations")
    number = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("sent", "Sent"), ("accepted", "Accepted"), ("declined", "Declined"), ("expired", "Expired"), ("converted", "Converted")], default="draft")
    currency = models.CharField(max_length=3)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    acceptance_token_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    converted_order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True, related_name="source_quotations")
    converted_invoice = models.ForeignKey("Invoice", on_delete=models.SET_NULL, blank=True, null=True, related_name="source_quotations")
    notes = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "number"], name="unique_business_quotation_number")]
        ordering = ["-created_at"]


class QuotationLine(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)


class Invoice(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="invoices")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="invoices")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True, related_name="invoices")
    number = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("issued", "Issued"), ("partially_paid", "Partially paid"), ("paid", "Paid"), ("void", "Void"), ("overdue", "Overdue")], default="draft")
    currency = models.CharField(max_length=3)
    issued_at = models.DateField(blank=True, null=True)
    due_at = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "number"], name="unique_business_invoice_number")]
        ordering = ["-created_at"]

    @property
    def balance_due(self):
        return self.grand_total - self.amount_paid


class InvoiceLine(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)


class PaymentAllocation(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payment_allocations")
    payment_attempt = models.ForeignKey(PaymentAttempt, on_delete=models.SET_NULL, blank=True, null=True, related_name="invoice_allocations")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=120, blank=True)
    received_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payment_allocations")
    created_at = models.DateTimeField(auto_now_add=True)


class ExpenseCategory(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="expense_categories")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_expense_category")]


class Expense(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="expenses")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, blank=True, null=True, related_name="expenses")
    receipt = models.ForeignKey(BusinessAsset, on_delete=models.SET_NULL, blank=True, null=True, related_name="expenses")
    description = models.CharField(max_length=240)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    incurred_at = models.DateField()
    payment_method = models.CharField(max_length=40, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_expenses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-incurred_at", "-id"]
