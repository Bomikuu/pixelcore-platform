from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from businesses.models import BusinessAsset
from content.hero import validate_hero_slides, public_hero_assets

from .models import (
    Category, Offering, OfferingCostComponent, OfferingFoodProfile, OfferingMedia,
    OfferingOption, OfferingVariant, OptionGroup, ProductCollection, ProductProfile,
    VariantDimension, VariantValue,
)


def validate_string_list(value, label="values", maximum=30):
    if not isinstance(value, list) or len(value) > maximum or any(not isinstance(item, str) or not item.strip() or len(item) > 80 for item in value):
        raise serializers.ValidationError(f"Use no more than {maximum} short text {label}.")
    return list(dict.fromkeys(item.strip() for item in value))


def validate_key_value_document(value, label, maximum=40):
    if not isinstance(value, dict) or len(value) > maximum:
        raise serializers.ValidationError(f"{label} must contain no more than {maximum} entries.")
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip() or len(key) > 80 or isinstance(item, (dict, list)) or len(str(item)) > 300:
            raise serializers.ValidationError(f"Each {label.lower()} entry needs a short key and simple value.")
    return value


class ProductProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductProfile
        fields = ["brand", "tags", "materials", "care_instructions", "shipping_weight_grams", "shipping_dimensions", "size_guide", "specifications", "seo_title", "seo_description", "card_hover_enabled", "card_gallery_enabled", "storefront_highlighted", "reservation_enabled", "rental_enabled", "reservation_terms", "rental_terms"]

    def validate_tags(self, value): return validate_string_list(value, "tags")
    def validate_shipping_dimensions(self, value): return validate_key_value_document(value, "Shipping dimensions", 6)
    def validate_size_guide(self, value): return validate_key_value_document(value, "Size guide", 30)
    def validate_specifications(self, value): return validate_key_value_document(value, "Specifications")


class VariantValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantValue
        fields = ["public_id", "label", "swatch_color", "sort_order"]
        read_only_fields = ["public_id"]

    def validate_swatch_color(self, value):
        if value and (len(value) != 7 or value[0] != "#" or any(character not in "0123456789abcdefABCDEF" for character in value[1:])):
            raise serializers.ValidationError("Use a six-digit hex color such as #1c786a.")
        return value.lower()


class VariantDimensionSerializer(serializers.ModelSerializer):
    values = VariantValueSerializer(many=True)

    class Meta:
        model = VariantDimension
        fields = ["public_id", "name", "display_type", "sort_order", "values"]
        read_only_fields = ["public_id"]


class OfferingMediaSerializer(serializers.ModelSerializer):
    asset_public_id = serializers.SlugRelatedField(source="asset", slug_field="public_id", queryset=BusinessAsset.objects.all())
    variant_public_id = serializers.SlugRelatedField(source="variant", slug_field="public_id", queryset=OfferingVariant.objects.all(), required=False, allow_null=True)
    url = serializers.SerializerMethodField()
    alt_text = serializers.CharField(source="asset.alt_text", read_only=True)
    processing_status = serializers.CharField(source="asset.processing_status", read_only=True)

    class Meta:
        model = OfferingMedia
        fields = ["public_id", "asset_public_id", "variant_public_id", "role", "sort_order", "url", "alt_text", "processing_status"]
        read_only_fields = ["public_id", "url", "alt_text", "processing_status"]

    def validate(self, attrs):
        business = self.context["business"]
        offering = self.context.get("offering") or getattr(self.instance, "offering", None)
        asset = attrs.get("asset", getattr(self.instance, "asset", None))
        variant = attrs.get("variant", getattr(self.instance, "variant", None))
        role = attrs.get("role", getattr(self.instance, "role", "gallery"))
        if not offering or offering.business_id != business.id or asset.business_id != business.id:
            raise serializers.ValidationError("Choose product media owned by this business.")
        if variant and variant.offering_id != offering.id:
            raise serializers.ValidationError({"variant_public_id": "Choose a variant of this product."})
        if role in {"cover", "gallery", "hover", "poster"} and asset.asset_type != "image":
            raise serializers.ValidationError({"asset_public_id": "This media role requires an image."})
        if role == "model" and (asset.asset_type != "model" or asset.processing_status != "ready"):
            raise serializers.ValidationError({"asset_public_id": "Choose an approved GLB model."})
        return attrs

    def get_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.asset.file.url) if request else obj.asset.file.url


class ProductCollectionSerializer(serializers.ModelSerializer):
    offering_public_ids = serializers.SlugRelatedField(source="offerings", slug_field="public_id", queryset=Offering.objects.all(), many=True, required=False)
    cover_asset_public_id = serializers.SlugRelatedField(source="cover_asset", slug_field="public_id", queryset=BusinessAsset.objects.all(), required=False, allow_null=True)
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductCollection
        fields = ["public_id", "name", "slug", "description", "cover_asset_public_id", "cover_url", "offering_public_ids", "hero_settings", "sort_order", "is_published", "created_at", "updated_at"]
        read_only_fields = ["public_id", "cover_url", "created_at", "updated_at"]
        extra_kwargs = {"slug": {"required": False}}

    def validate(self, attrs):
        business = self.context["business"]
        if attrs.get("cover_asset") and (attrs["cover_asset"].business_id != business.id or attrs["cover_asset"].asset_type != "image"):
            raise serializers.ValidationError({"cover_asset_public_id": "Choose an image from this business."})
        if any(offering.business_id != business.id for offering in attrs.get("offerings", [])):
            raise serializers.ValidationError({"offering_public_ids": "Choose products from this business."})
        settings = attrs.get("hero_settings", getattr(self.instance, "hero_settings", {})) or {}
        if not isinstance(settings, dict) or set(settings) - {"enabled", "heading", "body", "offering_ids", "autoplay", "slides"}:
            raise serializers.ValidationError({"hero_settings": "Use only the supported collection hero settings."})
        enabled = settings.get("enabled", True)
        autoplay = settings.get("autoplay", True)
        offering_ids = settings.get("offering_ids", [])
        if not isinstance(enabled, bool) or not isinstance(autoplay, bool):
            raise serializers.ValidationError({"hero_settings": "Enabled and autoplay must use true or false."})
        if not isinstance(offering_ids, list) or len(offering_ids) > 5:
            raise serializers.ValidationError({"hero_settings": "Choose no more than five hero products."})
        selected = attrs.get("offerings")
        if selected is None and self.instance:
            selected = list(self.instance.offerings.all())
        selected_ids = {str(item.public_id) for item in (selected or [])}
        if any(str(identifier) not in selected_ids for identifier in offering_ids):
            raise serializers.ValidationError({"hero_settings": "Hero products must belong to this collection."})
        heading = str(settings.get("heading", "")).strip()
        body = str(settings.get("body", "")).strip()
        if len(heading) > 180 or len(body) > 600:
            raise serializers.ValidationError({"hero_settings": "Keep the heading under 180 characters and description under 600."})
        attrs["hero_settings"] = {"enabled": enabled, "heading": heading, "body": body, "offering_ids": [str(value) for value in offering_ids], "autoplay": autoplay, "slides": validate_hero_slides(settings.get('slides', []), business)}
        return attrs

    def get_cover_url(self, obj):
        return obj.cover_asset.file.url if obj.cover_asset_id else ""


class PublicProductCollectionSerializer(serializers.ModelSerializer):
    hero_assets = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    offering_public_ids = serializers.SerializerMethodField()
    hero_settings = serializers.SerializerMethodField()

    class Meta:
        model = ProductCollection
        fields = ["public_id", "name", "slug", "description", "cover_url", "offering_public_ids", "hero_settings", "hero_assets"]

    def get_cover_url(self, obj): return obj.cover_asset.file.url if obj.cover_asset_id else ""
    def get_offering_public_ids(self, obj): return [str(value) for value in obj.offerings.filter(status="published").values_list("public_id", flat=True)]
    def get_hero_settings(self, obj):
        settings = obj.hero_settings or {}
        published_ids = set(self.get_offering_public_ids(obj))
        return {
            "enabled": settings.get("enabled", True),
            "heading": settings.get("heading", ""),
            "body": settings.get("body", ""),
            "offering_ids": [str(value) for value in settings.get("offering_ids", []) if str(value) in published_ids],
            "autoplay": settings.get("autoplay", True),
            "slides": settings.get('slides', []),
        }

    def get_hero_assets(self, obj):
        return public_hero_assets(obj.business, (obj.hero_settings or {}).get('slides', []))


class OfferingOptionSerializer(serializers.ModelSerializer):
    group_public_id = serializers.SlugRelatedField(source="group", slug_field="public_id", queryset=OptionGroup.objects.all())
    class Meta:
        model = OfferingOption
        fields = ["public_id", "group_public_id", "name", "price_delta", "cost_delta", "is_active", "sort_order"]
        read_only_fields = ["public_id"]
    def validate_group_public_id(self, group):
        if group.business_id != self.context["business"].id: raise serializers.ValidationError("Choose an option group from this business.")
        return group


class OptionGroupSerializer(serializers.ModelSerializer):
    offering_public_id = serializers.SlugRelatedField(source="offering", slug_field="public_id", queryset=Offering.objects.all())
    options = OfferingOptionSerializer(many=True, read_only=True)
    class Meta:
        model = OptionGroup
        fields = ["public_id", "offering_public_id", "name", "minimum_choices", "maximum_choices", "is_required", "sort_order", "options"]
        read_only_fields = ["public_id", "options"]
    def validate(self, attrs):
        offering = attrs.get("offering", getattr(self.instance, "offering", None))
        if not offering or offering.business_id != self.context["business"].id: raise serializers.ValidationError({"offering_public_id": "Choose an offering from this business."})
        minimum = attrs.get("minimum_choices", getattr(self.instance, "minimum_choices", 0)); maximum = attrs.get("maximum_choices", getattr(self.instance, "maximum_choices", 1))
        if maximum < 1 or minimum > maximum: raise serializers.ValidationError("Choice limits are invalid.")
        return attrs


class OfferingFoodProfileSerializer(serializers.ModelSerializer):
    offering_public_id = serializers.SlugRelatedField(source="offering", slug_field="public_id", queryset=Offering.objects.all())
    class Meta:
        model = OfferingFoodProfile
        fields = ["public_id", "offering_public_id", "serving_label", "calories", "protein_grams", "carbohydrate_grams", "fat_grams", "allergens", "ingredients"]
        read_only_fields = ["public_id"]
    def validate_offering_public_id(self, offering):
        business = self.context["business"]
        if offering.business_id != business.id or business.industry_preset != "restaurant": raise serializers.ValidationError("Food profiles require a restaurant-preset offering from this business.")
        return offering


class OfferingCostComponentSerializer(serializers.ModelSerializer):
    offering_public_id = serializers.SlugRelatedField(source="offering", slug_field="public_id", queryset=Offering.objects.all())
    extended_cost = serializers.SerializerMethodField()
    class Meta:
        model = OfferingCostComponent
        fields = ["public_id", "offering_public_id", "name", "quantity", "unit", "unit_cost", "extended_cost"]
        read_only_fields = ["public_id", "extended_cost"]
    def validate_offering_public_id(self, offering):
        if offering.business_id != self.context["business"].id: raise serializers.ValidationError("Choose an offering from this business.")
        return offering
    def get_extended_cost(self, obj): return obj.quantity * obj.unit_cost


class CategorySerializer(serializers.ModelSerializer):
    parent_public_id = serializers.SlugRelatedField(
        source="parent", slug_field="public_id", queryset=Category.objects.all(), required=False, allow_null=True
    )
    cover_asset_public_id = serializers.SlugRelatedField(source="cover_asset", slug_field="public_id", queryset=BusinessAsset.objects.all(), required=False, allow_null=True)
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["public_id", "name", "slug", "description", "parent_public_id", "cover_asset_public_id", "cover_url", "sort_order", "show_in_header", "header_order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["public_id", "cover_url", "created_at", "updated_at"]
        extra_kwargs = {"slug": {"required": False}}

    def validate(self, attrs):
        parent = attrs.get("parent")
        if parent and parent.business_id != self.context["business"].id:
            raise serializers.ValidationError({"parent_public_id": "Choose a parent category from this business."})
        cover = attrs.get("cover_asset")
        if cover and (cover.business_id != self.context["business"].id or cover.asset_type != "image" or cover.processing_status != "ready"):
            raise serializers.ValidationError({"cover_asset_public_id": "Choose a ready image from this business."})
        return attrs

    def get_cover_url(self, obj):
        if not obj.cover_asset_id:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.cover_asset.file.url) if request else obj.cover_asset.file.url


class OfferingVariantSerializer(serializers.ModelSerializer):
    option_values = VariantValueSerializer(many=True, read_only=True)
    class Meta:
        model = OfferingVariant
        fields = ["public_id", "name", "sku", "barcode", "price", "unit_cost", "compare_at_price", "attributes", "combination_key", "option_values", "is_active", "sort_order"]
        read_only_fields = ["public_id"]


class OfferingSerializer(serializers.ModelSerializer):
    category_public_id = serializers.SlugRelatedField(
        source="category", slug_field="public_id", queryset=Category.objects.all(), required=False, allow_null=True
    )
    asset_public_ids = serializers.SlugRelatedField(
        source="assets", slug_field="public_id", queryset=BusinessAsset.objects.all(), many=True, required=False
    )
    digital_asset_public_id = serializers.SlugRelatedField(
        source="digital_asset", slug_field="public_id", queryset=BusinessAsset.objects.all(), required=False, allow_null=True, write_only=True
    )
    variants = OfferingVariantSerializer(many=True, read_only=True)
    option_groups = OptionGroupSerializer(many=True, read_only=True)
    food_profile = OfferingFoodProfileSerializer(read_only=True)
    calculated_unit_cost = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True, allow_null=True)
    product_profile = ProductProfileSerializer(required=False)
    collections = ProductCollectionSerializer(many=True, read_only=True)
    variant_dimensions = VariantDimensionSerializer(many=True, read_only=True)
    ordered_media = OfferingMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Offering
        fields = [
            "public_id", "category_public_id", "category_name", "name", "slug", "summary", "description", "offering_type",
            "status", "fulfillment_type", "base_price", "compare_at_price", "tax_rate", "sku", "track_inventory",
            "duration_minutes", "capacity", "asset_public_ids", "digital_asset_public_id", "variants", "option_groups", "food_profile", "product_profile", "collections", "variant_dimensions", "ordered_media", "calculated_unit_cost", "media", "metadata", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]
        extra_kwargs = {"slug": {"required": False}}

    def validate(self, attrs):
        product_profile = attrs.pop("product_profile", None)
        if product_profile is not None:
            self.context["product_profile"] = product_profile
        business = self.context["business"]
        category = attrs.get("category")
        if category and category.business_id != business.id:
            raise serializers.ValidationError({"category_public_id": "Choose a category from this business."})
        for asset in attrs.get("assets", []):
            if asset.business_id != business.id:
                raise serializers.ValidationError({"asset_public_ids": "Choose assets from this business."})
        if attrs.get("digital_asset") and attrs["digital_asset"].business_id != business.id:
            raise serializers.ValidationError({"digital_asset_public_id": "Choose an asset from this business."})
        offering_type = attrs.get("offering_type", getattr(self.instance, "offering_type", None))
        duration = attrs.get("duration_minutes", getattr(self.instance, "duration_minutes", None))
        if offering_type == "service" and not duration:
            raise serializers.ValidationError({"duration_minutes": "Services require a duration."})
        if offering_type == "digital" and attrs.get("status", getattr(self.instance, "status", "draft")) == "published" and not attrs.get("digital_asset", getattr(self.instance, "digital_asset", None)):
            raise serializers.ValidationError({"digital_asset_public_id": "Published digital products require a protected delivery asset."})
        return attrs

    def _save_product_profile(self, offering):
        profile = self.context.pop("product_profile", None)
        if profile is not None:
            if profile.get("storefront_highlighted"):
                ProductProfile.objects.filter(business=offering.business, storefront_highlighted=True).exclude(offering=offering).update(storefront_highlighted=False)
            ProductProfile.objects.update_or_create(business=offering.business, offering=offering, defaults=profile)

    @transaction.atomic
    def create(self, validated_data):
        offering = super().create(validated_data)
        self._save_product_profile(offering)
        return offering

    @transaction.atomic
    def update(self, instance, validated_data):
        offering = super().update(instance, validated_data)
        self._save_product_profile(offering)
        return offering

    def get_calculated_unit_cost(self, obj):
        return sum((item.quantity * item.unit_cost for item in obj.cost_components.all()), 0)

    def get_media(self, obj):
        request = self.context.get("request")
        return [
            {
                "public_id": str(asset.public_id),
                "url": request.build_absolute_uri(asset.file.url) if request else asset.file.url,
                "alt_text": asset.alt_text,
            }
            for asset in obj.assets.filter(asset_type="image")
        ]


class PublicOfferingSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", allow_null=True)
    variants = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    option_groups = serializers.SerializerMethodField()
    food_profile = OfferingFoodProfileSerializer(read_only=True)
    product_profile = ProductProfileSerializer(read_only=True)
    collections = serializers.SerializerMethodField()
    variant_dimensions = VariantDimensionSerializer(many=True, read_only=True)
    ordered_media = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    request_options = serializers.SerializerMethodField()
    reservation_activity = serializers.SerializerMethodField()

    class Meta:
        model = Offering
        fields = [
            "public_id", "name", "slug", "summary", "description", "offering_type", "fulfillment_type",
            "base_price", "compare_at_price", "tax_rate", "duration_minutes", "capacity", "category", "variants", "option_groups", "food_profile", "product_profile", "collections", "variant_dimensions", "ordered_media", "availability", "media", "request_options", "reservation_activity",
        ]

    def get_request_options(self, obj):
        from commerce.product_requests import request_options
        return request_options(obj)

    def get_reservation_activity(self, obj):
        count = getattr(obj, "active_reservation_count", None)
        if count is None:
            count = obj.product_requests.filter(
                kind="reservation", status="held", expires_at__gt=timezone.now()
            ).values("email").distinct().count()
        if count < 2:
            return None
        return {"minimum_count": 2, "label": "2+ people have reserved this"}

    def get_media(self, obj):
        return [
            {"public_id": str(asset.public_id), "url": asset.file.url, "alt_text": asset.alt_text}
            for asset in obj.assets.filter(asset_type="image")
        ]

    def get_variants(self, obj):
        return [{
            "public_id": str(variant.public_id), "name": variant.name, "sku": variant.sku,
            "price": str(variant.price), "compare_at_price": str(variant.compare_at_price) if variant.compare_at_price is not None else None,
            "attributes": variant.attributes,
            "option_values": [{"public_id": str(value.public_id), "label": value.label, "swatch_color": value.swatch_color} for value in variant.option_values.all()],
            "is_active": True,
        } for variant in obj.variants.all() if variant.is_active]

    def get_option_groups(self, obj):
        return [{
            "public_id": str(group.public_id), "name": group.name, "minimum_choices": group.minimum_choices,
            "maximum_choices": group.maximum_choices, "is_required": group.is_required, "sort_order": group.sort_order,
            "options": [{"public_id": str(option.public_id), "name": option.name, "price_delta": str(option.price_delta), "is_active": True, "sort_order": option.sort_order} for option in group.options.all() if option.is_active],
        } for group in obj.option_groups.all()]

    def get_collections(self, obj):
        return [{"public_id": str(item.public_id), "name": item.name, "slug": item.slug} for item in obj.collections.filter(is_published=True)]

    def get_ordered_media(self, obj):
        media = []
        for item in obj.ordered_media.select_related("asset", "variant"):
            if item.asset.processing_status != "ready" or (item.role == "model" and item.asset.asset_type != "model"):
                continue
            media.append({
                "public_id": str(item.public_id), "role": item.role, "sort_order": item.sort_order,
                "variant_public_id": str(item.variant.public_id) if item.variant_id else None,
                "url": item.asset.file.url, "alt_text": item.asset.alt_text,
            })
        return media

    def get_availability(self, obj):
        if not obj.track_inventory:
            return "available"
        balances = [balance.available for variant in obj.variants.all() for balance in variant.inventory_balances.all()]
        return "available" if any(value > 0 for value in balances) else "out_of_stock"
