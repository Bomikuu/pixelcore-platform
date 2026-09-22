from datetime import timedelta

from rest_framework import serializers
from django.utils import timezone

from businesses.models import BusinessAsset, BusinessLocation
from catalog.models import OfferingVariant
from commerce.models import Customer, Order
from .models import (
    Expense, ExpenseCategory, InventoryBalance, Invoice, InvoiceLine, PaymentAllocation,
    PurchaseOrder, PurchaseOrderLine, Quotation, QuotationLine, StockMovement, Supplier, SupplierProduct,
)
from .services import create_invoice, create_quotation, next_document_number


def business_asset_url(asset, request=None):
    if not asset:
        return ""
    url = asset.file.url
    return request.build_absolute_uri(url) if request else url


def product_image_url(variant, request=None):
    variant_media = list(variant.ordered_media.all())
    offering_media = [item for item in variant.offering.ordered_media.all() if item.variant_id is None]
    candidates = variant_media + offering_media
    for role in ("cover", "gallery", "hover", "poster"):
        media = next(
            (
                item for item in candidates
                if item.role == role and item.asset.asset_type == "image" and item.asset.processing_status == "ready"
            ),
            None,
        )
        if media:
            return business_asset_url(media.asset, request)
    return ""


class InventoryBalanceSerializer(serializers.ModelSerializer):
    variant_public_id = serializers.SlugRelatedField(source="variant", slug_field="public_id", queryset=OfferingVariant.objects.all())
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all())
    offering_name = serializers.CharField(source="variant.offering.name", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    barcode = serializers.CharField(source="variant.barcode", read_only=True)
    unit_cost = serializers.DecimalField(source="variant.unit_cost", max_digits=12, decimal_places=2, read_only=True)
    sale_price = serializers.DecimalField(source="variant.price", max_digits=12, decimal_places=2, read_only=True)
    preferred_supplier_public_id = serializers.SlugRelatedField(
        source="preferred_supplier",
        slug_field="public_id",
        queryset=Supplier.objects.all(),
        required=False,
        allow_null=True,
    )
    preferred_supplier_name = serializers.CharField(source="preferred_supplier.name", read_only=True, allow_null=True)
    preferred_supplier_image_url = serializers.SerializerMethodField()
    available = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)
    image_url = serializers.SerializerMethodField()
    attention_status = serializers.SerializerMethodField()
    attention_message = serializers.SerializerMethodField()

    class Meta:
        model = InventoryBalance
        fields = [
            "public_id", "variant_public_id", "location_public_id", "location_name", "offering_name", "variant_name",
            "sku", "barcode", "image_url", "unit_cost", "sale_price", "on_hand", "reserved", "available", "low_stock_threshold",
            "reorder_quantity", "target_stock_level", "bin_location", "preferred_supplier_public_id",
            "preferred_supplier_name", "preferred_supplier_image_url", "last_counted_at", "notes", "attention_status",
            "attention_message", "updated_at",
        ]
        read_only_fields = ["public_id", "on_hand", "reserved", "available", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        variant = attrs.get("variant", getattr(self.instance, "variant", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        supplier = attrs.get("preferred_supplier", getattr(self.instance, "preferred_supplier", None))
        if not variant or not location or variant.offering.business_id != business.id or location.business_id != business.id:
            raise serializers.ValidationError("Variant and location must belong to this business.")
        if supplier and supplier.business_id != business.id:
            raise serializers.ValidationError("Choose a preferred supplier from this business.")
        for field in ("low_stock_threshold", "reorder_quantity", "target_stock_level"):
            value = attrs.get(field, getattr(self.instance, field, 0) if self.instance else 0)
            if value < 0:
                raise serializers.ValidationError({field: "Enter zero or a positive quantity."})
        threshold = attrs.get("low_stock_threshold", getattr(self.instance, "low_stock_threshold", 0) if self.instance else 0)
        target = attrs.get("target_stock_level", getattr(self.instance, "target_stock_level", 0) if self.instance else 0)
        if target and threshold > target:
            raise serializers.ValidationError({"target_stock_level": "Target stock must be at least the low-stock threshold."})
        return attrs

    def get_image_url(self, obj):
        return product_image_url(obj.variant, self.context.get("request"))

    def get_preferred_supplier_image_url(self, obj):
        supplier = obj.preferred_supplier
        return business_asset_url(supplier.image if supplier else None, self.context.get("request"))

    def get_attention_status(self, obj):
        if obj.available <= 0:
            return "critical"
        if obj.available <= obj.low_stock_threshold:
            return "warning"
        if not obj.preferred_supplier_id:
            return "setup"
        return "clear"

    def get_attention_message(self, obj):
        if obj.available <= 0:
            return "Out of stock"
        if obj.available <= obj.low_stock_threshold:
            return "Reorder stock"
        if not obj.preferred_supplier_id:
            return "Add preferred supplier"
        return "Stock healthy"


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["public_id", "movement_type", "quantity_delta", "reference_type", "reference_id", "note", "created_at"]


class SupplierProductSerializer(serializers.ModelSerializer):
    supplier_public_id = serializers.SlugRelatedField(source="supplier", slug_field="public_id", queryset=Supplier.objects.all())
    variant_public_id = serializers.SlugRelatedField(source="variant", slug_field="public_id", queryset=OfferingVariant.objects.all())
    offering_name = serializers.CharField(source="variant.offering.name", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SupplierProduct
        fields = [
            "public_id", "supplier_public_id", "variant_public_id", "offering_name", "variant_name", "sku", "image_url",
            "supplier_sku", "supplier_product_name", "last_unit_cost", "minimum_order_quantity", "lead_time_days",
            "is_active", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]

    def get_image_url(self, obj):
        return product_image_url(obj.variant, self.context.get("request"))

    def validate(self, attrs):
        business = self.context["business"]
        supplier = attrs.get("supplier", getattr(self.instance, "supplier", None))
        variant = attrs.get("variant", getattr(self.instance, "variant", None))
        if not supplier or supplier.business_id != business.id:
            raise serializers.ValidationError({"supplier_public_id": "Choose a supplier from this business."})
        if not variant or variant.offering.business_id != business.id:
            raise serializers.ValidationError({"variant_public_id": "Choose a product variant from this business."})
        if attrs.get("minimum_order_quantity", getattr(self.instance, "minimum_order_quantity", 1) if self.instance else 1) <= 0:
            raise serializers.ValidationError({"minimum_order_quantity": "Enter a quantity greater than zero."})
        return attrs


class SupplierSerializer(serializers.ModelSerializer):
    purchase_order_count = serializers.IntegerField(read_only=True)
    open_purchase_order_count = serializers.IntegerField(read_only=True)
    expense_count = serializers.IntegerField(read_only=True)
    preferred_inventory_count = serializers.IntegerField(read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    image_public_id = serializers.SlugRelatedField(
        source="image",
        slug_field="public_id",
        queryset=BusinessAsset.objects.all(),
        required=False,
        allow_null=True,
    )
    image_url = serializers.SerializerMethodField()
    products = SupplierProductSerializer(source="supplied_products", many=True, read_only=True)
    attention_status = serializers.SerializerMethodField()
    attention_message = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        exclude = ["id", "business", "image"]
        read_only_fields = ["public_id", "created_at", "updated_at"]

    def validate_image_public_id(self, image):
        if image.business_id != self.context["business"].id or image.asset_type != "image":
            raise serializers.ValidationError("Choose an image from this business.")
        return image

    def get_image_url(self, obj):
        return business_asset_url(obj.image, self.context.get("request"))

    def get_attention_status(self, obj):
        if not obj.is_active:
            return "muted"
        if not obj.email and not obj.phone:
            return "warning"
        product_count = getattr(obj, "product_count", None)
        if (obj.supplied_products.count() if product_count is None else product_count) == 0:
            return "setup"
        return "clear"

    def get_attention_message(self, obj):
        if not obj.is_active:
            return "Inactive supplier"
        if not obj.email and not obj.phone:
            return "Add contact details"
        product_count = getattr(obj, "product_count", None)
        if (obj.supplied_products.count() if product_count is None else product_count) == 0:
            return "Add supplied products"
        return "Supplier ready"

class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    variant_public_id = serializers.SlugRelatedField(source="variant", slug_field="public_id", queryset=OfferingVariant.objects.all())
    offering_name = serializers.CharField(source="variant.offering.name", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    image_url = serializers.SerializerMethodField()
    inventory_balance_public_id = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "public_id", "variant_public_id", "offering_name", "variant_name", "sku", "image_url", "inventory_balance_public_id",
            "description", "quantity_ordered", "quantity_received", "unit_cost",
        ]
        read_only_fields = ["public_id", "quantity_received"]

    def get_image_url(self, obj):
        return product_image_url(obj.variant, self.context.get("request"))

    def get_inventory_balance_public_id(self, obj):
        balance = InventoryBalance.objects.filter(
            business=obj.purchase_order.business,
            location=obj.purchase_order.location,
            variant=obj.variant,
        ).only("public_id").first()
        return balance.public_id if balance else None


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_public_id = serializers.SlugRelatedField(source="supplier", slug_field="public_id", queryset=Supplier.objects.all())
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all())
    lines = PurchaseOrderLineSerializer(many=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    supplier_image_url = serializers.SerializerMethodField()
    location_name = serializers.CharField(source="location.name", read_only=True)
    total_amount = serializers.SerializerMethodField()
    remaining_units = serializers.SerializerMethodField()
    receiving_progress = serializers.SerializerMethodField()
    attention_status = serializers.SerializerMethodField()
    attention_message = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "public_id", "number", "supplier_public_id", "supplier_name", "supplier_image_url", "location_public_id", "location_name", "status",
            "ordered_at", "expected_at", "received_at", "supplier_reference", "shipping_method", "shipping_address", "notes", "lines",
            "total_amount", "remaining_units", "receiving_progress", "attention_status", "attention_message", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "number", "received_at", "created_at", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        supplier = attrs.get("supplier", getattr(self.instance, "supplier", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        if not supplier or not location or supplier.business_id != business.id or location.business_id != business.id:
            raise serializers.ValidationError("Supplier and location must belong to this business.")
        for line in attrs.get("lines", []):
            if line["variant"].offering.business_id != business.id:
                raise serializers.ValidationError("Every purchase order variant must belong to this business.")
        ordered_at = attrs.get("ordered_at", getattr(self.instance, "ordered_at", None))
        expected_at = attrs.get("expected_at", getattr(self.instance, "expected_at", None))
        if ordered_at and expected_at and expected_at < ordered_at:
            raise serializers.ValidationError({"expected_at": "Expected date cannot be before the ordered date."})
        status_value = attrs.get("status", getattr(self.instance, "status", "draft"))
        if status_value in {"partially_received", "received"} and (not self.instance or status_value != self.instance.status):
            raise serializers.ValidationError({"status": "Use Receive stock to update receiving status and inventory together."})
        return attrs

    def create(self, validated_data):
        lines = validated_data.pop("lines")
        business = validated_data["business"]
        purchase_order = PurchaseOrder.objects.create(number=next_document_number(business, "purchase_order", "PO"), **validated_data)
        for line in lines:
            PurchaseOrderLine.objects.create(purchase_order=purchase_order, **line)
            SupplierProduct.objects.update_or_create(
                business=business,
                supplier=purchase_order.supplier,
                variant=line["variant"],
                defaults={
                    "supplier_product_name": line["description"],
                    "last_unit_cost": line["unit_cost"],
                    "lead_time_days": purchase_order.supplier.lead_time_days,
                    "is_active": True,
                },
            )
        return purchase_order

    def get_total_amount(self, obj):
        return sum((line.quantity_ordered * line.unit_cost for line in obj.lines.all()), 0)

    def get_supplier_image_url(self, obj):
        return business_asset_url(obj.supplier.image, self.context.get("request"))

    def get_remaining_units(self, obj):
        return sum((line.quantity_ordered - line.quantity_received for line in obj.lines.all()), 0)

    def get_receiving_progress(self, obj):
        ordered = sum((line.quantity_ordered for line in obj.lines.all()), 0)
        received = sum((line.quantity_received for line in obj.lines.all()), 0)
        return round(float(received / ordered * 100), 1) if ordered else 0

    def get_attention_status(self, obj):
        if obj.status in {"received", "cancelled"}:
            return "clear"
        if obj.expected_at and obj.expected_at < timezone.localdate():
            return "critical"
        if obj.status == "partially_received":
            return "warning"
        if obj.status == "draft":
            return "setup"
        return "clear"

    def get_attention_message(self, obj):
        if obj.status == "received":
            return "Fully received"
        if obj.status == "cancelled":
            return "Cancelled"
        if obj.expected_at and obj.expected_at < timezone.localdate():
            return "Delivery overdue"
        if obj.status == "partially_received":
            return "Partially received"
        if obj.status == "draft":
            return "Issue this order"
        return "Awaiting delivery"


class QuotationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationLine
        fields = ["public_id", "description", "quantity", "unit_price", "tax_rate", "line_total"]
        read_only_fields = ["public_id", "line_total"]


class QuotationSerializer(serializers.ModelSerializer):
    customer_public_id = serializers.SlugRelatedField(source="customer", slug_field="public_id", queryset=Customer.objects.all())
    lines = QuotationLineSerializer(many=True)
    converted_order_public_id = serializers.UUIDField(source="converted_order.public_id", read_only=True)
    converted_invoice_public_id = serializers.UUIDField(source="converted_invoice.public_id", read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    attention_status = serializers.SerializerMethodField()
    attention_message = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = ["public_id", "number", "customer_public_id", "customer_name", "customer_email", "status", "currency", "subtotal", "tax_total", "grand_total", "expires_at", "accepted_at", "notes", "lines", "converted_order_public_id", "converted_invoice_public_id", "attention_status", "attention_message", "created_at", "updated_at"]
        read_only_fields = ["public_id", "number", "currency", "subtotal", "tax_total", "grand_total", "accepted_at", "created_at", "updated_at"]

    def validate_customer_public_id(self, customer):
        if customer.business_id != self.context["business"].id:
            raise serializers.ValidationError("Choose a customer from this business.")
        return customer

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.email

    def get_attention_status(self, obj):
        if obj.status in {"accepted", "converted"}:
            return "clear"
        if obj.status in {"declined", "expired"}:
            return "muted"
        if obj.expires_at and obj.expires_at <= timezone.now():
            return "critical"
        if obj.expires_at and obj.expires_at <= timezone.now() + timedelta(days=3):
            return "warning"
        return "setup" if obj.status == "draft" else "clear"

    def get_attention_message(self, obj):
        if obj.status == "converted":
            return "Converted"
        if obj.status == "accepted":
            return "Accepted"
        if obj.status == "declined":
            return "Declined"
        if obj.status == "expired" or (obj.expires_at and obj.expires_at <= timezone.now()):
            return "Expired"
        if obj.expires_at and obj.expires_at <= timezone.now() + timedelta(days=3):
            return "Expires soon"
        if obj.status == "draft":
            return "Send to customer"
        return "Awaiting response"

    def create(self, validated_data):
        lines = validated_data.pop("lines")
        quotation, token = create_quotation(
            validated_data.pop("business"),
            validated_data.pop("customer"),
            lines,
            validated_data,
            self.context["request"].user,
        )
        quotation.acceptance_token = token
        return quotation


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ["public_id", "description", "quantity", "unit_price", "tax_rate", "line_total"]
        read_only_fields = ["public_id", "line_total"]


class PaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = ["public_id", "amount", "reference", "received_at", "created_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    customer_public_id = serializers.SlugRelatedField(source="customer", slug_field="public_id", queryset=Customer.objects.all())
    order_public_id = serializers.SlugRelatedField(source="order", slug_field="public_id", queryset=Order.objects.all(), required=False, allow_null=True)
    lines = InvoiceLineSerializer(many=True)
    payment_allocations = PaymentAllocationSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    document_notice = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    attention_status = serializers.SerializerMethodField()
    attention_message = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "public_id", "number", "customer_public_id", "customer_name", "customer_email", "order_public_id", "status", "currency", "issued_at", "due_at",
            "subtotal", "tax_total", "grand_total", "amount_paid", "balance_due", "notes", "lines", "payment_allocations",
            "document_notice", "attention_status", "attention_message", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "number", "currency", "subtotal", "tax_total", "grand_total", "amount_paid", "balance_due", "document_notice", "created_at", "updated_at"]

    def get_document_notice(self, obj):
        return "Operational commercial record only. This document is not represented as a BIR-authorized invoice or receipt."

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.email

    def get_attention_status(self, obj):
        if obj.status in {"paid", "void"} or obj.balance_due <= 0:
            return "clear"
        if obj.due_at and obj.due_at < timezone.localdate():
            return "critical"
        if obj.due_at and obj.due_at <= timezone.localdate() + timedelta(days=3):
            return "warning"
        return "setup" if obj.status == "draft" else "clear"

    def get_attention_message(self, obj):
        if obj.status == "paid" or obj.balance_due <= 0:
            return "Paid"
        if obj.status == "void":
            return "Void"
        if obj.due_at and obj.due_at < timezone.localdate():
            return "Payment overdue"
        if obj.due_at and obj.due_at <= timezone.localdate() + timedelta(days=3):
            return "Payment due soon"
        if obj.status == "draft":
            return "Issue this invoice"
        if obj.amount_paid > 0:
            return "Partially paid"
        return "Awaiting payment"

    def validate(self, attrs):
        business = self.context["business"]
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        order = attrs.get("order", getattr(self.instance, "order", None))
        if not customer or customer.business_id != business.id or (order and order.business_id != business.id):
            raise serializers.ValidationError("Customer and order must belong to this business.")
        return attrs

    def create(self, validated_data):
        lines = validated_data.pop("lines")
        return create_invoice(
            validated_data.pop("business"),
            validated_data.pop("customer"),
            lines,
            validated_data,
            self.context["request"].user,
        )


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        exclude = ["id", "business"]
        read_only_fields = ["public_id"]


class ExpenseSerializer(serializers.ModelSerializer):
    category_public_id = serializers.SlugRelatedField(source="category", slug_field="public_id", queryset=ExpenseCategory.objects.all())
    supplier_public_id = serializers.SlugRelatedField(source="supplier", slug_field="public_id", queryset=Supplier.objects.all(), required=False, allow_null=True)
    receipt_public_id = serializers.SlugRelatedField(source="receipt", slug_field="public_id", queryset=BusinessAsset.objects.all(), required=False, allow_null=True)
    receipt_name = serializers.CharField(source="receipt.title", read_only=True, allow_null=True)
    receipt_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, allow_null=True)
    supplier_image_url = serializers.SerializerMethodField()
    attention_status = serializers.SerializerMethodField()
    attention_message = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = ["public_id", "category_public_id", "category_name", "supplier_public_id", "supplier_name", "supplier_image_url", "receipt_public_id", "receipt_name", "receipt_url", "description", "amount", "tax_amount", "incurred_at", "payment_method", "reference", "attention_status", "attention_message", "created_at", "updated_at"]
        read_only_fields = ["public_id", "created_at", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        category = attrs.get("category", getattr(self.instance, "category", None))
        supplier = attrs.get("supplier", getattr(self.instance, "supplier", None))
        receipt = attrs.get("receipt", getattr(self.instance, "receipt", None))
        resources = [item for item in (category, supplier, receipt) if item]
        if not category:
            raise serializers.ValidationError("Choose an expense category from this business.")
        if any(resource.business_id != business.id for resource in resources):
            raise serializers.ValidationError("Expense resources must belong to this business.")
        if receipt and receipt.asset_type not in {"image", "document"}:
            raise serializers.ValidationError({"receipt_public_id": "Attach an image or PDF receipt."})
        return attrs

    def create(self, validated_data):
        return Expense.objects.create(created_by=self.context["request"].user, **validated_data)

    def get_attention_status(self, obj):
        if not obj.receipt_id:
            return "warning"
        if not obj.reference:
            return "setup"
        return "clear"

    def get_supplier_image_url(self, obj):
        supplier = obj.supplier
        return business_asset_url(supplier.image if supplier else None, self.context.get("request"))

    def get_receipt_url(self, obj):
        return business_asset_url(obj.receipt, self.context.get("request"))

    def get_attention_message(self, obj):
        if not obj.receipt_id:
            return "Attach receipt"
        if not obj.reference:
            return "Add payment reference"
        return "Evidence complete"
