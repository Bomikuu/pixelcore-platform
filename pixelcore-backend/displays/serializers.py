import re
import math

from rest_framework import serializers

from businesses.models import BusinessAsset, BusinessDevice, BusinessLocation
from catalog.models import Offering
from catalog.serializers import OfferingSerializer
from .models import DisplayDeviceAssignment, DisplayPublication


HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
ALLOWED_FONTS = {"manrope", "newsreader", "poppins", "montserrat", "playfair", "system"}
ALLOWED_ELEMENT_TYPES = {"business", "heading", "subtitle", "text", "offering", "offering_group", "image", "social_footer"}
ALLOWED_STYLE_FIELDS = {"font_family", "font_size", "font_weight", "color", "text_align", "background_asset_id"}


def validate_display_settings(value):
    if not isinstance(value, dict):
        raise serializers.ValidationError("Display settings must be an object.")
    if len(str(value)) > 200_000:
        raise serializers.ValidationError("Display settings exceed the 200 KB limit.")
    forbidden = {"script", "javascript", "shader", "css", "html", "url", "srcdoc"}
    def walk(node, depth=0):
        if depth > 8: raise serializers.ValidationError("Display settings are nested too deeply.")
        if isinstance(node, dict):
            for key, child in node.items():
                if str(key).lower() in forbidden: raise serializers.ValidationError(f"Unsupported display field: {key}.")
                walk(child, depth + 1)
        elif isinstance(node, list):
            if len(node) > 200: raise serializers.ValidationError("A display list exceeds its item limit.")
            for child in node: walk(child, depth + 1)
        elif not isinstance(node, (str, int, float, bool, type(None))):
            raise serializers.ValidationError("Display settings contain an unsupported value.")
    walk(value)
    builder = value.get("builder", {})
    if not isinstance(builder, dict): raise serializers.ValidationError("Display builder settings must be an object.")
    slides = builder.get("slides", [])
    if not isinstance(slides, list): raise serializers.ValidationError("Display slides must be a list.")
    if len(slides) > 12: raise serializers.ValidationError("A display supports at most 12 slides.")
    for slide in slides:
        if not isinstance(slide, dict): raise serializers.ValidationError("Each display slide must be an object.")
        elements = slide.get("elements", [])
        if not isinstance(elements, list): raise serializers.ValidationError("Display elements must be a list.")
        if len(elements) > 60: raise serializers.ValidationError("A slide supports at most 60 elements.")
        for element in elements:
            if not isinstance(element, dict): raise serializers.ValidationError("Each display element must be an object.")
            if element.get("type") not in ALLOWED_ELEMENT_TYPES: raise serializers.ValidationError("The display contains an unsupported element type.")
            if len(str(element.get("id", ""))) > 80 or len(str(element.get("content", ""))) > 300:
                raise serializers.ValidationError("A display element exceeds its text limit.")
            for field, minimum, maximum in (("x", 0, 100), ("y", 0, 100), ("width", 4, 100), ("height", 4, 100), ("rotation", -180, 180), ("z_index", 0, 1000)):
                number = element.get(field, minimum)
                if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number < minimum or number > maximum:
                    raise serializers.ValidationError(f"Display element {field} is outside its allowed range.")
            style = element.get("style", {})
            if not isinstance(style, dict) or set(style) - ALLOWED_STYLE_FIELDS:
                raise serializers.ValidationError("The display contains unsupported style settings.")
            if style.get("font_family") and style["font_family"] not in ALLOWED_FONTS:
                raise serializers.ValidationError("Choose an approved display font.")
            if style.get("color") and not HEX.fullmatch(str(style["color"])):
                raise serializers.ValidationError("Display colors must use six-digit hex values.")
            if style.get("text_align") and style["text_align"] not in {"left", "center", "right"}:
                raise serializers.ValidationError("Choose a supported text alignment.")
    for color_field in ("background", "foreground"):
        if value.get(color_field) and not HEX.fullmatch(str(value[color_field])):
            raise serializers.ValidationError({color_field: "Use a six-digit hex color."})
    return value


class DisplayPublicationSerializer(serializers.ModelSerializer):
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all(), required=False, allow_null=True)
    background_asset_public_id = serializers.SlugRelatedField(source="background_asset", slug_field="public_id", queryset=BusinessAsset.objects.all(), required=False, allow_null=True)
    settings = serializers.JSONField(validators=[validate_display_settings])
    offerings = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()
    background_asset_url = serializers.SerializerMethodField()
    business_identity = serializers.SerializerMethodField()
    assets = serializers.SerializerMethodField()

    class Meta:
        model = DisplayPublication
        fields = ["public_id", "business_identity", "location_public_id", "name", "kind", "template", "schema_version", "settings", "offering_ids", "background_asset_public_id", "background_asset_url", "assets", "offerings", "public_url", "is_active", "is_published", "published_at", "created_at", "updated_at"]
        read_only_fields = ["public_id", "business_identity", "schema_version", "background_asset_url", "assets", "offerings", "public_url", "published_at", "created_at", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        for name in ("location", "background_asset"):
            item = attrs.get(name, getattr(self.instance, name, None))
            if item and item.business_id != business.id: raise serializers.ValidationError({f"{name}_public_id": "Choose an item from this business."})
        ids = attrs.get("offering_ids", getattr(self.instance, "offering_ids", []))
        if len(ids) > 200 or Offering.objects.filter(business=business, public_id__in=ids).count() != len(set(ids)):
            raise serializers.ValidationError({"offering_ids": "Choose up to 200 offerings from this business."})
        if attrs.get("template", getattr(self.instance, "template", "")) == "poster_menu" and business.industry_preset != "restaurant":
            raise serializers.ValidationError({"template": "Poster Menu is available when the restaurant preset is selected."})
        return attrs

    def get_offerings(self, obj):
        queryset = Offering.objects.filter(business=obj.business, public_id__in=obj.offering_ids, status="published").prefetch_related("variants", "assets")
        return OfferingSerializer(queryset, many=True).data

    def get_public_url(self, obj):
        return f"/display/{obj.share_key}" if obj.is_published and obj.is_active else None

    def get_background_asset_url(self, obj):
        if not obj.background_asset:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.background_asset.file.url) if request else obj.background_asset.file.url

    def get_business_identity(self, obj):
        return {
            "display_name": obj.business.display_name,
            "currency": obj.business.currency,
        }

    def get_assets(self, obj):
        identifiers = set()
        builder = obj.settings.get("builder", {}) if isinstance(obj.settings, dict) else {}
        for slide in builder.get("slides", []):
            for element in slide.get("elements", []):
                if element.get("asset_id"):
                    identifiers.add(str(element["asset_id"]))
                style = element.get("style", {})
                if isinstance(style, dict) and style.get("background_asset_id"):
                    identifiers.add(str(style["background_asset_id"]))
        request = self.context.get("request")
        output = []
        for asset in BusinessAsset.objects.filter(business=obj.business, public_id__in=identifiers, asset_type="image"):
            file_url = request.build_absolute_uri(asset.file.url) if request else asset.file.url
            output.append({"public_id": str(asset.public_id), "title": asset.title, "alt_text": asset.alt_text, "file_url": file_url})
        return output


class DisplayAssignmentSerializer(serializers.Serializer):
    device_public_id = serializers.UUIDField()
    def validate_device_public_id(self, identifier):
        device = BusinessDevice.objects.filter(public_id=identifier, business=self.context["business"], device_type="signage", is_active=True).first()
        if not device: raise serializers.ValidationError("Choose an active signage device from this business.")
        return device
