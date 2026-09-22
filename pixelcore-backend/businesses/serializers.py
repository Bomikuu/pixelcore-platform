import json
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers
from scheduling.models import ResourceLayout

from .models import (
    AccountProfile,
    AuditEvent,
    Business,
    BusinessAsset,
    BusinessCard,
    BusinessCapability,
    BusinessEvent,
    BusinessDevice,
    DeviceLink,
    BusinessInvitation,
    BusinessLocation,
    BusinessMembership,
    default_modules,
)
from .identity import default_identity_config, normalize_identity_config, referenced_asset_ids
from .services import bootstrap_business, set_capabilities, unique_location_code


User = get_user_model()
ALLOWED_MODULES = set(default_modules())
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
BUSINESS_CARD_SOCIAL_PLATFORMS = {
    "facebook",
    "instagram",
    "linkedin",
    "tiktok",
    "x",
    "youtube",
}


def validate_uploaded_image(value):
    if not value:
        return value
    content_type = getattr(value, "content_type", "")
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError("Use a JPG, PNG, or WebP image.")
    if value.size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError("Images must be 5 MB or smaller.")
    return value


class BrandingField(serializers.JSONField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError("Branding must be valid JSON.") from exc
        return normalize_identity_config(super().to_internal_value(data))

    def to_representation(self, value):
        return normalize_identity_config(value or {})


class BrandingAssetsMixin:
    branding_assets = serializers.SerializerMethodField()

    def get_branding_assets(self, obj):
        identifiers = referenced_asset_ids(obj.branding or {})
        if not identifiers:
            return {}
        request = self.context.get("request")
        assets = obj.assets.filter(public_id__in=identifiers, processing_status="ready")
        return {
            str(asset.public_id): {
                "public_id": str(asset.public_id),
                "title": asset.title,
                "asset_type": asset.asset_type,
                "url": asset.file.url,
            }
            for asset in assets
        }


class BusinessIdentitySerializer(BrandingAssetsMixin, serializers.ModelSerializer):
    branding = BrandingField(required=False)
    enabled_modules = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(ALLOWED_MODULES)),
        required=False,
    )
    logo = serializers.ImageField(required=False, allow_null=True, validators=[validate_uploaded_image])
    favicon = serializers.ImageField(required=False, allow_null=True, validators=[validate_uploaded_image])
    cover_image = serializers.ImageField(required=False, allow_null=True, validators=[validate_uploaded_image])
    branding_assets = serializers.SerializerMethodField()
    branding_defaults = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "public_id",
            "industry_preset",
            "display_name",
            "legal_name",
            "slug",
            "industry",
            "tagline",
            "description",
            "status",
            "contact_email",
            "contact_phone",
            "website_url",
            "address",
            "city",
            "region",
            "postal_code",
            "country",
            "timezone",
            "locale",
            "currency",
            "currency_locked_at",
            "tax_id",
            "tax_status",
            "prices_include_tax",
            "logo",
            "favicon",
            "cover_image",
            "branding",
            "branding_assets",
            "branding_defaults",
            "enabled_modules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "status", "currency_locked_at", "branding_assets", "branding_defaults", "created_at", "updated_at"]

    def get_branding_defaults(self, obj):
        return default_identity_config()

    def validate_enabled_modules(self, value):
        modules = list(dict.fromkeys(value))
        return modules

    def validate_branding(self, value):
        business = self.instance
        from content.hero import validate_hero_slides
        validate_hero_slides(value["storefront"]["marketplace"]["slides"], business=business)
        asset_ids = referenced_asset_ids(value)
        if asset_ids and business is None:
            raise serializers.ValidationError("Create the business before assigning identity media.")
        if business and asset_ids:
            assets = {str(asset.public_id): asset for asset in business.assets.filter(public_id__in=asset_ids, processing_status="ready")}
            missing = asset_ids - set(assets)
            if missing:
                raise serializers.ValidationError("Every referenced media item must be a ready asset from this business.")
            storefront = value["storefront"]
            expected = [
                (storefront["background"]["asset_id"], {"image"}, "Storefront backgrounds use image assets."),
                (storefront["popup"]["asset_id"], {"image"}, "Popup media uses an image asset."),
                (storefront["footer"]["logo_asset_id"], {"image"}, "Footer logos use image assets."),
                (storefront["hero"]["poster_asset_id"], {"image"}, "Hero posters use image assets."),
            ]
            hero = storefront["hero"]
            if hero["asset_id"]:
                expected.append((hero["asset_id"], {"image"} if hero["type"] == "image" else {"video"} if hero["type"] == "video" else {"model"} if hero["type"] == "three" else {"image", "video", "model"}, "The selected hero media does not match its background type."))
            for asset_id, allowed_types, message in expected:
                if asset_id and assets[asset_id].asset_type not in allowed_types:
                    raise serializers.ValidationError(message)
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        capability_codes = list(
            instance.capabilities.exclude(status="disabled").order_by("code").values_list("code", flat=True)
        )
        data["enabled_modules"] = capability_codes or instance.enabled_modules
        return data

    def validate_country(self, value):
        value = value.upper()
        if len(value) != 2 or not value.isalpha():
            raise serializers.ValidationError("Use a two-letter country code.")
        return value

    def validate_currency(self, value):
        value = value.upper()
        if len(value) != 3 or not value.isalpha():
            raise serializers.ValidationError("Use a three-letter currency code.")
        if self.instance and self.instance.currency_locked_at and value != self.instance.currency:
            raise serializers.ValidationError("Currency is locked because this business has financial transactions.")
        return value

    def create(self, validated_data):
        enabled_modules = validated_data.pop("enabled_modules", default_modules())
        business = Business.objects.create(
            created_by=self.context["request"].user,
            **validated_data,
        )
        BusinessMembership.objects.create(
            business=business,
            user=self.context["request"].user,
            role="owner",
        )
        bootstrap_business(business)
        set_capabilities(business, enabled_modules, self.context["request"].user)
        return business

    def update(self, instance, validated_data):
        enabled_modules = validated_data.pop("enabled_modules", None)
        instance = super().update(instance, validated_data)
        if enabled_modules is not None:
            set_capabilities(instance, enabled_modules, self.context["request"].user)
        return instance


class PublicBusinessIdentitySerializer(BrandingAssetsMixin, serializers.ModelSerializer):
    branding = BrandingField(read_only=True)
    logo = serializers.SerializerMethodField()
    favicon = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    branding_assets = serializers.SerializerMethodField()
    public_booking_enabled = serializers.SerializerMethodField()
    booking_intro = serializers.SerializerMethodField()
    advance_booking_days = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "public_id",
            "industry_preset",
            "display_name",
            "slug",
            "industry",
            "tagline",
            "description",
            "contact_email",
            "contact_phone",
            "website_url",
            "city",
            "region",
            "country",
            "timezone",
            "locale",
            "currency",
            "tax_status",
            "prices_include_tax",
            "logo",
            "favicon",
            "cover_image",
            "branding",
            "branding_assets",
            "public_booking_enabled",
            "booking_intro",
            "advance_booking_days",
            "enabled_modules",
            "updated_at",
        ]

    def _file_url(self, obj, field):
        value = getattr(obj, field)
        return value.url if value else None

    def get_logo(self, obj):
        return self._file_url(obj, "logo")

    def get_favicon(self, obj):
        return self._file_url(obj, "favicon")

    def get_cover_image(self, obj):
        return self._file_url(obj, "cover_image")

    def _schedule_settings(self, obj):
        try:
            return obj.scheduling_settings
        except ObjectDoesNotExist:
            return None

    def get_public_booking_enabled(self, obj):
        settings_record = self._schedule_settings(obj)
        return settings_record.public_booking_enabled if settings_record else True

    def get_booking_intro(self, obj):
        settings_record = self._schedule_settings(obj)
        return settings_record.public_intro if settings_record else ""

    def get_advance_booking_days(self, obj):
        settings_record = self._schedule_settings(obj)
        return settings_record.advance_booking_days if settings_record else 31


class MembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = BusinessMembership
        fields = ["id", "email", "name", "role", "status", "joined_at"]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.email or obj.user.username


class BusinessCardSerializer(serializers.ModelSerializer):
    background_asset_public_id = serializers.SlugRelatedField(
        source="background_asset",
        slug_field="public_id",
        queryset=BusinessAsset.objects.all(),
        required=False,
        allow_null=True,
    )
    background_image_url = serializers.SerializerMethodField()
    custom_font_asset_public_id = serializers.SlugRelatedField(
        source="custom_font_asset",
        slug_field="public_id",
        queryset=BusinessAsset.objects.all(),
        required=False,
        allow_null=True,
    )
    custom_font_url = serializers.SerializerMethodField()
    business_name = serializers.CharField(source="business.display_name", read_only=True)
    business_tagline = serializers.CharField(source="business.tagline", read_only=True)
    business_website_url = serializers.URLField(source="business.website_url", read_only=True)
    business_address = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    public_path = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()

    class Meta:
        model = BusinessCard
        fields = [
            "public_id",
            "display_name",
            "job_title",
            "headline",
            "email",
            "phone",
            "style",
            "orientation",
            "font_style",
            "color_mode",
            "typography_mode",
            "heading_font",
            "body_font",
            "accent_font",
            "custom_font_asset_public_id",
            "custom_font_url",
            "background_color",
            "text_color",
            "accent_color",
            "border_color",
            "ornament_color",
            "social_links",
            "show_social_links",
            "show_qr",
            "background_type",
            "background_asset_public_id",
            "background_image_url",
            "background_apply_to",
            "background_image_fit",
            "background_image_position",
            "background_overlay",
            "background_overlay_strength",
            "show_email",
            "show_phone",
            "show_business_address",
            "is_published",
            "business_name",
            "business_tagline",
            "business_website_url",
            "business_address",
            "logo_url",
            "public_path",
            "theme",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "public_id",
            "background_image_url",
            "business_name",
            "business_tagline",
            "business_website_url",
            "business_address",
            "logo_url",
            "public_path",
            "theme",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        business = self.context.get("business") or getattr(
            self.instance,
            "business",
            None,
        )
        if business:
            self.fields["background_asset_public_id"].queryset = business.assets.filter(
                asset_type="image",
                processing_status="ready",
            )
            self.fields["custom_font_asset_public_id"].queryset = business.assets.filter(
                asset_type="font",
                processing_status="ready",
            )

    def get_business_address(self, obj):
        return ", ".join(
            part
            for part in [
                obj.business.address,
                obj.business.city,
                obj.business.region,
                obj.business.postal_code,
                obj.business.country,
            ]
            if part
        )

    def validate_social_links(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Use a list of social profiles.")
        if len(value) > 4:
            raise serializers.ValidationError("Add no more than four social profiles.")

        profiles = []
        used_platforms = set()
        for index, item in enumerate(value):
            if not isinstance(item, dict) or set(item) != {"platform", "url"}:
                raise serializers.ValidationError(
                    f"Social profile {index + 1} needs a platform and URL."
                )
            platform = str(item.get("platform", "")).strip().lower()
            if platform not in BUSINESS_CARD_SOCIAL_PLATFORMS:
                raise serializers.ValidationError(
                    f"Social profile {index + 1} uses an unsupported platform."
                )
            if platform in used_platforms:
                raise serializers.ValidationError(
                    f"Add only one {platform} profile."
                )
            url = str(item.get("url", "")).strip()
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc or len(url) > 500:
                raise serializers.ValidationError(
                    f"Social profile {index + 1} needs a complete HTTPS URL."
                )
            used_platforms.add(platform)
            profiles.append({"platform": platform, "url": url})
        return profiles

    def get_logo_url(self, obj):
        if not obj.business.logo:
            return ""
        return obj.business.logo.url

    def get_background_image_url(self, obj):
        asset = obj.background_asset
        if (
            obj.background_type != "image"
            or not asset
            or asset.asset_type != "image"
            or asset.processing_status != "ready"
        ):
            return ""
        return asset.file.url

    def get_custom_font_url(self, obj):
        asset = obj.custom_font_asset
        if (
            not asset
            or asset.asset_type != "font"
            or asset.processing_status != "ready"
        ):
            return ""
        return asset.file.url

    def validate(self, attrs):
        attrs = super().validate(attrs)
        font_asset = attrs.get(
            "custom_font_asset",
            getattr(self.instance, "custom_font_asset", None),
        )
        font_fields = [
            attrs.get("heading_font", getattr(self.instance, "heading_font", "cormorant")),
            attrs.get("body_font", getattr(self.instance, "body_font", "manrope")),
            attrs.get("accent_font", getattr(self.instance, "accent_font", "great_vibes")),
        ]
        typography_mode = attrs.get(
            "typography_mode",
            getattr(self.instance, "typography_mode", "style"),
        )
        if typography_mode == "custom" and "custom" in font_fields and not font_asset:
            raise serializers.ValidationError(
                {"custom_font_asset_public_id": "Upload a WOFF2 font before selecting Custom."}
            )
        return attrs

    def get_public_path(self, obj):
        return f"/card/{obj.public_id}" if obj.pk and obj.is_published else ""

    def get_theme(self, obj):
        branding = obj.business.branding or {}
        return {
            "primary_color": branding.get("primary_color", "#165B4C"),
            "secondary_color": branding.get("secondary_color", "#17362F"),
            "accent_color": branding.get("accent_color", "#D8922B"),
            "background_color": branding.get("background_color", "#FAF9F5"),
            "text_color": branding.get("text_color", "#17312B"),
        }


class PublicBusinessCardSerializer(BusinessCardSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.show_email:
            data["email"] = ""
        if not instance.show_phone:
            data["phone"] = ""
        if not instance.show_business_address:
            data["business_address"] = ""
        if not instance.show_social_links:
            data["social_links"] = []
        for private_field in [
            "background_asset_public_id",
            "custom_font_asset_public_id",
            "show_email",
            "show_phone",
            "show_business_address",
            "show_social_links",
            "is_published",
            "created_at",
            "updated_at",
        ]:
            data.pop(private_field, None)
        return data


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account already uses this email.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not re.fullmatch(r"[0-9+().\-\s]{7,32}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        if AccountProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("An account already uses this phone number.")
        return value

    def validate_username(self, value):
        value = value.strip()
        if value and User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate(self, attrs):
        confirmation = attrs.pop("password_confirm", None)
        if confirmation is not None and confirmation != attrs["password"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data.pop("phone")
        username = validated_data.pop("username", "")
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        user = User(username=username or email, email=email, is_active=False, **validated_data)
        user.set_password(password)
        user.save()
        AccountProfile.objects.create(user=user, phone=phone)
        return user


class OnboardingSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=160)
    country = serializers.CharField(max_length=2, default="PH")
    industry_preset = serializers.ChoiceField(choices=["general", "restaurant", "retail", "services", "hybrid"], default="general")
    location_name = serializers.CharField(max_length=120, default="Main location")
    enabled_modules = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(ALLOWED_MODULES)),
        default=default_modules,
    )

    def validate_country(self, value):
        value = value.upper()
        if len(value) != 2 or not value.isalpha():
            raise serializers.ValidationError("Use a two-letter country code.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        if user.business_memberships.filter(status="active").exists():
            raise serializers.ValidationError("This account already has an active business.")
        country = validated_data.pop("country")
        location_name = validated_data.pop("location_name")
        enabled_modules = list(dict.fromkeys(validated_data.pop("enabled_modules")))
        regional_defaults = {
            "PH": {"currency": "PHP", "timezone": "Asia/Manila", "locale": "en-PH"},
        }.get(country, {"currency": "USD", "timezone": "UTC", "locale": "en"})
        business = Business.objects.create(created_by=user, country=country, **regional_defaults, **validated_data)
        BusinessMembership.objects.create(business=business, user=user, role="owner")
        bootstrap_business(business)
        location = business.locations.filter(is_primary=True).first()
        if location:
            location.name = location_name
            location.code = unique_location_code(business, location_name)
            location.save(update_fields=["name", "code", "updated_at"])
        set_capabilities(business, enabled_modules, user)
        return business


class BusinessCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCapability
        fields = ["code", "status", "settings", "updated_at"]
        read_only_fields = ["code", "updated_at"]


class BusinessLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessLocation
        fields = [
            "public_id", "name", "code", "address", "city", "region", "postal_code",
            "country", "timezone", "latitude", "longitude", "is_primary", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]
        extra_kwargs = {"code": {"required": False}}

    def create(self, validated_data):
        business = self.context["business"]
        validated_data.setdefault("code", unique_location_code(business, validated_data["name"]))
        if validated_data.get("is_primary"):
            business.locations.update(is_primary=False)
        return BusinessLocation.objects.create(business=business, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_primary"):
            instance.business.locations.exclude(pk=instance.pk).update(is_primary=False)
        return super().update(instance, validated_data)

    def validate_latitude(self, value):
        if value is not None and not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value


class BusinessAssetSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = BusinessAsset
        fields = [
            "public_id", "title", "alt_text", "asset_type", "file", "file_url", "mime_type",
            "size_bytes", "metadata", "created_at",
            "processing_status", "validation_error",
        ]
        read_only_fields = ["public_id", "file_url", "mime_type", "size_bytes", "processing_status", "validation_error", "created_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def validate(self, attrs):
        upload = attrs.get("file")
        if upload:
            content_type = getattr(upload, "content_type", "application/octet-stream").lower()
            allowed = {
                "image": {"image/jpeg", "image/png", "image/webp", "image/avif"},
                "video": {"video/mp4", "video/webm"},
                "document": {"application/pdf"},
                "model": {"model/gltf-binary", "application/octet-stream"},
                "font": {
                    "font/woff2",
                    "application/font-woff2",
                    "application/octet-stream",
                },
            }
            asset_type = attrs.get("asset_type")
            if content_type not in allowed.get(asset_type, set()):
                raise serializers.ValidationError({"file": "The file type does not match the selected asset type."})
            maximum = {
                "image": 8,
                "video": 50,
                "document": 10,
                "model": 25,
                "font": 2,
            }[asset_type] * 1024 * 1024
            if upload.size > maximum:
                raise serializers.ValidationError({"file": f"This {asset_type} exceeds its upload limit."})
            if asset_type == "model" and not upload.name.lower().endswith(".glb"):
                raise serializers.ValidationError({"file": "Upload one self-contained .glb model."})
            if asset_type == "font":
                if not upload.name.lower().endswith(".woff2"):
                    raise serializers.ValidationError({"file": "Upload a WOFF2 font file."})
                position = upload.tell()
                header = upload.read(48)
                upload.seek(position)
                declared_length = int.from_bytes(header[8:12], "big") if len(header) >= 12 else 0
                if len(header) < 48 or header[:4] != b"wOF2" or declared_length != upload.size:
                    raise serializers.ValidationError(
                        {"file": "This file is not a valid self-contained WOFF2 font."}
                    )
        return attrs

    def create(self, validated_data):
        upload = validated_data["file"]
        asset_type = validated_data["asset_type"]
        processing_status = "processing" if asset_type == "model" else "ready"
        asset = BusinessAsset.objects.create(
            business=self.context["business"],
            uploaded_by=self.context["request"].user,
            mime_type=getattr(upload, "content_type", "application/octet-stream"),
            size_bytes=upload.size,
            processing_status=processing_status,
            **validated_data,
        )
        if asset_type == "model":
            from catalog.glb import validate_glb
            metadata, error = validate_glb(upload)
            asset.processing_status = "ready" if metadata else "rejected"
            asset.validation_error = error
            if metadata:
                asset.metadata = {**asset.metadata, **metadata}
            asset.save(update_fields=["processing_status", "validation_error", "metadata"])
        return asset

    def get_file_url(self, obj):
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class BusinessDeviceSerializer(serializers.ModelSerializer):
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all(), required=False, allow_null=True)

    class Meta:
        model = BusinessDevice
        fields = ["public_id", "location_public_id", "name", "device_type", "is_active", "configuration", "last_seen_at", "created_at", "updated_at"]
        read_only_fields = ["public_id", "last_seen_at", "created_at", "updated_at"]

    def validate_location_public_id(self, location):
        if location is None:
            return None
        if location.business_id != self.context["business"].id:
            raise serializers.ValidationError("Choose a location from this business.")
        return location

    def create(self, validated_data):
        return BusinessDevice.objects.create(
            business=self.context["business"],
            created_by=self.context["request"].user,
            **validated_data,
        )


class BusinessInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessInvitation
        fields = ["public_id", "email", "role", "status", "expires_at", "accepted_at", "created_at"]
        read_only_fields = ["public_id", "status", "expires_at", "accepted_at", "created_at"]

    def validate_role(self, value):
        if value not in {"admin", "manager", "staff"}:
            raise serializers.ValidationError(
                "Choose administrator, manager, or staff access."
            )
        return value


class DeviceLinkSerializer(serializers.ModelSerializer):
    source_device_public_id = serializers.SlugRelatedField(source="source_device", slug_field="public_id", queryset=BusinessDevice.objects.all())
    target_device_public_id = serializers.SlugRelatedField(source="target_device", slug_field="public_id", queryset=BusinessDevice.objects.all())
    source_device_name = serializers.CharField(source="source_device.name", read_only=True)
    target_device_name = serializers.CharField(source="target_device.name", read_only=True)

    class Meta:
        model = DeviceLink
        fields = ["public_id", "source_device_public_id", "source_device_name", "target_device_public_id", "target_device_name", "link_type", "is_active", "created_at", "updated_at"]
        read_only_fields = ["public_id", "source_device_name", "target_device_name", "created_at", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        source = attrs.get("source_device", getattr(self.instance, "source_device", None))
        target = attrs.get("target_device", getattr(self.instance, "target_device", None))
        if not source or source.business_id != business.id or source.device_type != "pos" or not source.is_active:
            raise serializers.ValidationError({"source_device_public_id": "Choose an active POS station from this business."})
        if not target or target.business_id != business.id or target.device_type != "customer_display" or not target.is_active:
            raise serializers.ValidationError({"target_device_public_id": "Choose an active customer display from this business."})
        linked = DeviceLink.objects.filter(target_device=target).exclude(pk=getattr(self.instance, "pk", None)).exists()
        if linked:
            raise serializers.ValidationError({"target_device_public_id": "This display is already linked to a station."})
        if source.location_id and target.location_id and source.location_id != target.location_id:
            raise serializers.ValidationError("Linked devices must use the same location.")
        return attrs

    def create(self, validated_data):
        return DeviceLink.objects.create(
            business=self.context["business"],
            created_by=self.context["request"].user,
            **validated_data,
        )


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ["id", "actor_email", "action", "resource_type", "resource_id", "metadata", "created_at"]


class BusinessEventSerializer(serializers.ModelSerializer):
    resource_layout_public_id = serializers.SlugRelatedField(
        source="resource_layout",
        slug_field="public_id",
        queryset=ResourceLayout.objects.all(),
        required=False,
        allow_null=True,
    )
    resource_layout_name = serializers.CharField(source="resource_layout.name", read_only=True)

    class Meta:
        model = BusinessEvent
        fields = [
            "id",
            "title",
            "notes",
            "event_type",
            "status",
            "starts_at",
            "ends_at",
            "resource_layout_public_id",
            "resource_layout_name",
            "google_event_url",
            "google_sync_status",
            "google_synced_at",
            "google_sync_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "google_event_url",
            "google_sync_status",
            "google_synced_at",
            "google_sync_error",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if ends_at and starts_at and ends_at <= starts_at:
            raise serializers.ValidationError({"ends_at": "End time must be after the start time."})
        resource_layout = attrs.get("resource_layout", getattr(self.instance, "resource_layout", None))
        business = self.context.get("business")
        if resource_layout and business and resource_layout.business_id != business.id:
            raise serializers.ValidationError({"resource_layout_public_id": "Choose a venue layout from this business."})
        return attrs
