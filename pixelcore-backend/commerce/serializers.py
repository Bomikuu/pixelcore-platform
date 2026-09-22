from decimal import Decimal

from rest_framework import serializers

from businesses.google_calendar import encrypt_token
from businesses.models import BusinessLocation
from catalog.models import Category, Offering, OfferingOption, OfferingVariant
from catalog.serializers import OfferingSerializer
from .models import (
    Cart, CartItem, Customer, CustomerAddress, Discount, Fulfillment, Order, OrderItem,
    PaymentAttempt, PaymentConnection, Refund, SavedOffering, ShippingZone,
)
from .services import calculate_cart, configure_payment_connection


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        exclude = ["id", "customer"]
        read_only_fields = ["public_id"]


class CustomerSerializer(serializers.ModelSerializer):
    addresses = CustomerAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ["public_id", "email", "first_name", "last_name", "phone", "notes", "accepts_marketing", "addresses", "created_at", "updated_at"]
        read_only_fields = ["public_id", "created_at", "updated_at"]


class CustomerPortalProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100, allow_blank=False, required=False)
    last_name = serializers.CharField(max_length=100, allow_blank=True, required=False)
    phone = serializers.RegexField(
        r"^[0-9+(). -]{0,32}$",
        max_length=32,
        allow_blank=True,
        required=False,
    )

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "phone", "accepts_marketing"]


class CustomerPortalAddressSerializer(serializers.ModelSerializer):
    phone = serializers.RegexField(
        r"^[0-9+(). -]{0,32}$",
        max_length=32,
        allow_blank=True,
        required=False,
    )

    class Meta:
        model = CustomerAddress
        fields = [
            "public_id",
            "label",
            "recipient_name",
            "line1",
            "line2",
            "city",
            "region",
            "postal_code",
            "country",
            "phone",
            "is_default",
        ]
        read_only_fields = ["public_id"]

    def validate_country(self, value):
        value = value.strip().upper()
        if len(value) != 2 or not value.isalpha():
            raise serializers.ValidationError("Use a two-letter country code such as PH.")
        return value


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        exclude = ["id", "business"]
        read_only_fields = ["public_id"]


class DiscountSerializer(serializers.ModelSerializer):
    offering_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=500)
    category_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=500)
    scope_type = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        exclude = ["id", "business"]
        read_only_fields = ["public_id", "created_at", "updated_at"]

    def get_scope_type(self, obj):
        return "categories" if obj.category_ids else "products" if obj.offering_ids else "catalog"

    def validate(self, attrs):
        def current(key, default=None):
            return attrs.get(key, getattr(self.instance, key, default))
        value_type, value = current("value_type"), current("value", 0)
        if value <= 0 or (value_type == "percentage" and value > 100):
            raise serializers.ValidationError({"value": "Enter a positive value; percentage discounts cannot exceed 100."})
        automatic = current("is_automatic", False)
        code = str(current("code", "")).strip().upper()
        if automatic and code:
            raise serializers.ValidationError({"code": "Automatic discounts cannot also require a code."})
        if not automatic and not code:
            raise serializers.ValidationError({"code": "Add a promotion code."})
        duplicates = Discount.objects.filter(business=self.context["business"], code__iexact=code)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if code and duplicates.exists():
            raise serializers.ValidationError({"code": "This code is already used by another promotion."})
        attrs["code"] = code
        starts, ends = current("starts_at"), current("ends_at")
        if starts and ends and ends <= starts:
            raise serializers.ValidationError({"ends_at": "End time must be after start time."})
        for field, model in (("offering_ids", Offering), ("category_ids", Category)):
            ids = list(dict.fromkeys(str(value) for value in current(field, [])))
            if model.objects.filter(business=self.context["business"], public_id__in=ids).count() != len(ids):
                raise serializers.ValidationError({field: "Choose records from this business."})
            if field in attrs:
                attrs[field] = ids
        if current("offering_ids", []) and current("category_ids", []):
            raise serializers.ValidationError({"category_ids": "Choose either categories or individual products."})
        return attrs


class SavedOfferingSerializer(serializers.ModelSerializer):
    offering = serializers.SerializerMethodField()
    offering_public_id = serializers.SlugRelatedField(
        source="offering",
        slug_field="public_id",
        queryset=Offering.objects.all(),
        write_only=True,
    )

    class Meta:
        model = SavedOffering
        fields = ["public_id", "offering_public_id", "offering", "created_at"]
        read_only_fields = ["public_id", "offering", "created_at"]

    def validate_offering_public_id(self, offering):
        if offering.business_id != self.context["business"].id or offering.status != "published":
            raise serializers.ValidationError("Choose a published offering from this business.")
        return offering

    def get_offering(self, obj):
        from catalog.serializers import PublicOfferingSerializer
        return PublicOfferingSerializer(obj.offering, context=self.context).data


class CartItemSerializer(serializers.ModelSerializer):
    offering_public_id = serializers.UUIDField(source="offering.public_id")
    variant_public_id = serializers.UUIDField(source="variant.public_id", allow_null=True)
    name = serializers.CharField(source="offering.name", read_only=True)
    fulfillment_type = serializers.CharField(source="offering.fulfillment_type", read_only=True)

    class Meta:
        model = CartItem
        fields = ["public_id", "offering_public_id", "variant_public_id", "name", "fulfillment_type", "quantity", "unit_price", "tax_rate", "metadata"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    totals = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["public_id", "status", "currency", "fulfillment_type", "email", "expires_at", "items", "discount_code", "totals", "created_at", "updated_at"]

    discount_code = serializers.CharField(source="discount.code", read_only=True, allow_null=True)

    def get_totals(self, obj):
        return calculate_cart(obj, discount=obj.discount)


class CartUpdateSerializer(serializers.Serializer):
    discount_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    fulfillment_type = serializers.ChoiceField(choices=["delivery", "pickup", "digital", "booking", "none"], required=False)

    def validate_discount_code(self, value):
        from .services import active_discount
        if not value:
            return ""
        if not active_discount(self.context["cart"].business, value):
            raise serializers.ValidationError("This promotion code is invalid or expired.")
        return value.strip()


class CartItemInputSerializer(serializers.Serializer):
    offering_public_id = serializers.UUIDField()
    variant_public_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, max_value=999)
    metadata = serializers.DictField(required=False)
    option_public_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=30)

    def validate(self, attrs):
        business = self.context["cart"].business
        offering = Offering.objects.filter(public_id=attrs["offering_public_id"], business=business, status="published").first()
        if not offering:
            raise serializers.ValidationError({"offering_public_id": "This offering is not available."})
        variant = None
        if attrs.get("variant_public_id"):
            variant = OfferingVariant.objects.filter(public_id=attrs["variant_public_id"], offering=offering, is_active=True).first()
            if not variant:
                raise serializers.ValidationError({"variant_public_id": "This variant is not available."})
        elif offering.variants.filter(is_active=True).exists():
            raise serializers.ValidationError({"variant_public_id": "Choose a variant."})
        attrs["offering"] = offering
        attrs["variant"] = variant
        option_ids = attrs.pop("option_public_ids", [])
        options = list(OfferingOption.objects.filter(public_id__in=option_ids, group__offering=offering, is_active=True).select_related("group"))
        if len(options) != len(set(option_ids)):
            raise serializers.ValidationError({"option_public_ids": "One or more options are unavailable."})
        selected_by_group = {}
        for option in options: selected_by_group.setdefault(option.group_id, []).append(option)
        for group in offering.option_groups.prefetch_related("options"):
            count = len(selected_by_group.get(group.id, []))
            if count < group.minimum_choices or count > group.maximum_choices:
                raise serializers.ValidationError({"option_public_ids": f"Choose between {group.minimum_choices} and {group.maximum_choices} options for {group.name}."})
        attrs["options"] = options
        attrs["unit_price"] = (variant.price if variant else offering.base_price) + sum((option.price_delta for option in options), Decimal("0"))
        return attrs


class CheckoutSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    fulfillment_type = serializers.ChoiceField(choices=["delivery", "pickup", "digital", "booking", "none"])
    payment_method = serializers.ChoiceField(choices=["paymongo", "cod", "manual"])
    shipping_address = serializers.DictField(required=False)
    shipping_zone_public_id = serializers.UUIDField(required=False, allow_null=True)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    discount_code = serializers.CharField(max_length=40, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["fulfillment_type"] == "delivery" and not attrs.get("shipping_address"):
            raise serializers.ValidationError({"shipping_address": "A delivery address is required."})
        if attrs["fulfillment_type"] == "delivery":
            zone = ShippingZone.objects.filter(
                business=self.context["business"],
                public_id=attrs.pop("shipping_zone_public_id", None),
                is_active=True,
            ).first()
            if not zone:
                raise serializers.ValidationError({"shipping_zone_public_id": "Choose an available shipping zone."})
            attrs["shipping_zone"] = zone
        if attrs["payment_method"] == "cod" and attrs["fulfillment_type"] not in {"delivery", "pickup"}:
            raise serializers.ValidationError({"payment_method": "Cash on delivery is available only for delivery or pickup orders."})
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        exclude = ["id", "order", "offering", "variant"]

    def get_image_url(self, obj):
        if not obj.offering_id:
            return ""
        asset = obj.offering.assets.filter(asset_type="image").first()
        return asset.file.url if asset else ""


class FulfillmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fulfillment
        exclude = ["id", "order"]


class PaymentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAttempt
        exclude = ["id", "business", "order", "raw_status"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    fulfillments = FulfillmentSerializer(many=True, read_only=True)
    payment_attempts = PaymentAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "public_id", "number", "status", "payment_status", "payment_method", "fulfillment_type", "currency",
            "subtotal", "tax_total", "shipping_total", "discount_total", "grand_total", "customer_snapshot",
            "shipping_snapshot", "notes", "items", "fulfillments", "payment_attempts", "placed_at", "updated_at",
        ]


class PublicOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["public_id", "name", "sku", "quantity", "unit_price", "tax_rate", "line_total"]


class PublicOrderConfirmationSerializer(serializers.ModelSerializer):
    items = PublicOrderItemSerializer(many=True, read_only=True)
    fulfillments = serializers.SerializerMethodField()
    payment_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["public_id", "number", "status", "payment_status", "payment_method", "fulfillment_type", "currency", "subtotal", "tax_total", "shipping_total", "discount_total", "grand_total", "items", "fulfillments", "payment_attempts", "placed_at", "updated_at"]

    def get_fulfillments(self, obj):
        return [{"public_id": str(item.public_id), "fulfillment_type": item.fulfillment_type, "status": item.status, "tracking_reference": item.tracking_reference, "fulfilled_at": item.fulfilled_at} for item in obj.fulfillments.all()]

    def get_payment_attempts(self, obj):
        return [{"public_id": str(item.public_id), "provider": item.provider, "status": item.status, "amount": str(item.amount), "currency": item.currency, "updated_at": item.updated_at} for item in obj.payment_attempts.all()]
        read_only_fields = [
            "public_id", "number", "payment_method", "fulfillment_type", "currency", "subtotal", "tax_total",
            "shipping_total", "discount_total", "grand_total", "customer_snapshot", "shipping_snapshot", "placed_at", "updated_at",
        ]


class PaymentConnectionSerializer(serializers.ModelSerializer):
    secret_key = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    webhook_secret = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    configured = serializers.SerializerMethodField()

    class Meta:
        model = PaymentConnection
        fields = ["provider", "public_key", "secret_key", "webhook_secret", "is_live", "is_active", "configured", "updated_at"]
        read_only_fields = ["configured", "updated_at"]

    def get_configured(self, obj):
        return bool(obj.encrypted_secret_key and obj.encrypted_webhook_secret)

    def create(self, validated_data):
        secret_key = validated_data.pop("secret_key", "")
        webhook_secret = validated_data.pop("webhook_secret", "")
        if not secret_key or not webhook_secret:
            raise serializers.ValidationError("Secret key and webhook secret are required when connecting a provider.")
        return configure_payment_connection(self.context["business"], secret_key=secret_key, webhook_secret=webhook_secret, **validated_data)

    def update(self, instance, validated_data):
        secret_key = validated_data.pop("secret_key", None)
        webhook_secret = validated_data.pop("webhook_secret", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if secret_key:
            instance.encrypted_secret_key = encrypt_token(secret_key)
        if webhook_secret:
            instance.encrypted_webhook_secret = encrypt_token(webhook_secret)
        instance.save()
        return instance


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ["public_id", "amount", "reason", "provider_reference", "status", "created_at"]
        read_only_fields = ["public_id", "provider_reference", "status", "created_at"]
