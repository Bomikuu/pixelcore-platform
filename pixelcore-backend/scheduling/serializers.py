import re
from pathlib import Path

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from businesses.models import BusinessLocation, BusinessMembership
from catalog.models import Offering
from commerce.serializers import CustomerSerializer
from .models import (
    AvailabilityException,
    AvailabilityRule,
    Booking,
    EventGuest,
    EventMedia,
    EventParticipant,
    EventQuote,
    EventSchedule,
    EventStoryBlock,
    Resource,
    ResourceLayout,
    ResourceType,
    SchedulingSettings,
    ServiceAssignment,
    ServiceSession,
    StaffProfile,
    VenueEvent,
)


class StaffProfileSerializer(serializers.ModelSerializer):
    membership_id = serializers.PrimaryKeyRelatedField(source="membership", queryset=BusinessMembership.objects.all(), required=False, allow_null=True)
    has_attendance_pin = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            "public_id", "membership_id", "display_name", "profile_image", "profile_image_url", "email", "employee_code", "job_title", "employment_status",
            "hired_at", "emergency_contact_name", "emergency_contact_phone", "scheduled_start_time", "scheduled_end_time",
            "late_grace_minutes", "consecutive_late_threshold", "has_attendance_pin", "bio", "timezone", "is_bookable", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "employee_code", "profile_image_url", "has_attendance_pin", "created_at", "updated_at"]
        extra_kwargs = {"profile_image": {"write_only": True}}

    def get_profile_image_url(self, obj):
        if not obj.profile_image:
            return None
        request = self.context.get("request")
        url = obj.profile_image.url
        return request.build_absolute_uri(url) if request else url

    def validate_profile_image(self, upload):
        if upload is None:
            return None
        if upload.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Choose a profile photo up to 5 MB.")
        image = getattr(upload, "image", None)
        if image is None or image.format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError("Use a JPG, PNG, or WebP photo.")
        if max(image.size) > 4096:
            raise serializers.ValidationError("Use an image no larger than 4096 pixels per side.")
        return upload

    def get_has_attendance_pin(self, obj):
        return bool(obj.attendance_pin_digest)

    def validate(self, attrs):
        membership = attrs.get("membership")
        if membership and membership.business_id != self.context["business"].id:
            raise serializers.ValidationError({"membership_id": "Choose a member of this business."})
        start = attrs.get("scheduled_start_time", getattr(self.instance, "scheduled_start_time", None))
        end = attrs.get("scheduled_end_time", getattr(self.instance, "scheduled_end_time", None))
        if bool(start) != bool(end):
            raise serializers.ValidationError("Scheduled start and end must be provided together.")
        return attrs


class ResourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceType
        fields = ["public_id", "name", "singular_label", "plural_label", "icon", "is_active"]
        read_only_fields = ["public_id"]


class ResourceLayoutSerializer(serializers.ModelSerializer):
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all())

    class Meta:
        model = ResourceLayout
        fields = [
            "public_id",
            "location_public_id",
            "name",
            "layout_type",
            "description",
            "width",
            "height",
            "is_active",
        ]
        read_only_fields = ["public_id"]

    def validate_location_public_id(self, location):
        if location.business_id != self.context["business"].id:
            raise serializers.ValidationError("Choose a location from this business.")
        return location


class ResourceSerializer(serializers.ModelSerializer):
    resource_type_public_id = serializers.SlugRelatedField(source="resource_type", slug_field="public_id", queryset=ResourceType.objects.all())
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all())
    layout_public_id = serializers.SlugRelatedField(source="layout", slug_field="public_id", queryset=ResourceLayout.objects.all(), required=False, allow_null=True)
    type_name = serializers.CharField(source="resource_type.name", read_only=True)

    class Meta:
        model = Resource
        fields = [
            "public_id",
            "resource_type_public_id",
            "type_name",
            "location_public_id",
            "layout_public_id",
            "name",
            "element_type",
            "is_bookable",
            "capacity",
            "shape",
            "width",
            "height",
            "rotation",
            "position_x",
            "position_y",
            "is_active",
            "metadata",
        ]
        read_only_fields = ["public_id", "type_name"]

    def validate(self, attrs):
        business = self.context["business"]
        related = [attrs.get(name, getattr(self.instance, name, None)) for name in ("resource_type", "location", "layout")]
        if any(item and item.business_id != business.id for item in related):
            raise serializers.ValidationError("Resource type, location, and layout must belong to this business.")
        if related[2] and related[1] and related[2].location_id != related[1].id:
            raise serializers.ValidationError({"layout_public_id": "Choose a layout at the selected location."})
        for field in ("position_x", "position_y"):
            value = attrs.get(field, getattr(self.instance, field, 20))
            if value > 100:
                raise serializers.ValidationError({field: "Use a percentage from 0 to 100."})
        for field in ("width", "height"):
            value = attrs.get(field, getattr(self.instance, field, 16))
            if value < 4 or value > 80:
                raise serializers.ValidationError({field: "Use a percentage from 4 to 80."})
        rotation = attrs.get("rotation", getattr(self.instance, "rotation", 0))
        if rotation < -180 or rotation > 180:
            raise serializers.ValidationError({"rotation": "Use a rotation from -180 to 180 degrees."})
        return attrs


class SchedulingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedulingSettings
        fields = [
            "public_booking_enabled",
            "public_intro",
            "advance_booking_days",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_advance_booking_days(self, value):
        if value < 1 or value > 365:
            raise serializers.ValidationError("Choose a booking window from 1 to 365 days.")
        return value


class AvailabilityRuleSerializer(serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(source="staff", slug_field="public_id", queryset=StaffProfile.objects.all())
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all(), required=False, allow_null=True)

    class Meta:
        model = AvailabilityRule
        fields = ["public_id", "staff_public_id", "location_public_id", "weekday", "starts_at", "ends_at", "valid_from", "valid_until", "is_active"]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        business = self.context["business"]
        staff = attrs.get("staff", getattr(self.instance, "staff", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        weekday = attrs.get("weekday", getattr(self.instance, "weekday", 0))
        if not staff or staff.business_id != business.id or (location and location.business_id != business.id):
            raise serializers.ValidationError("Staff and location must belong to this business.")
        if weekday > 6 or (starts_at and ends_at and ends_at <= starts_at):
            raise serializers.ValidationError("Use a weekday from 0 to 6 and an end time after the start time.")
        return attrs


class AvailabilityExceptionSerializer(serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(source="staff", slug_field="public_id", queryset=StaffProfile.objects.all())

    class Meta:
        model = AvailabilityException
        fields = ["public_id", "staff_public_id", "starts_at", "ends_at", "exception_type", "reason"]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        staff = attrs.get("staff", getattr(self.instance, "staff", None))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if not staff or staff.business_id != self.context["business"].id:
            raise serializers.ValidationError({"staff_public_id": "Choose staff from this business."})
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({"ends_at": "End time must be after start time."})
        return attrs


class ServiceAssignmentSerializer(serializers.ModelSerializer):
    staff_public_id = serializers.SlugRelatedField(source="staff", slug_field="public_id", queryset=StaffProfile.objects.all())
    offering_public_id = serializers.SlugRelatedField(source="offering", slug_field="public_id", queryset=Offering.objects.all())
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all(), required=False, allow_null=True)

    class Meta:
        model = ServiceAssignment
        fields = ["public_id", "staff_public_id", "offering_public_id", "location_public_id", "price_override", "duration_override", "is_active"]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        business = self.context["business"]
        staff = attrs.get("staff", getattr(self.instance, "staff", None))
        offering = attrs.get("offering", getattr(self.instance, "offering", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        related = [item for item in (staff, offering, location) if item]
        if not staff or not offering or any(item.business_id != business.id for item in related) or offering.offering_type != "service":
            raise serializers.ValidationError("Assignment resources must be service resources from this business.")
        return attrs


class ServiceSessionSerializer(serializers.ModelSerializer):
    offering_public_id = serializers.SlugRelatedField(source="offering", slug_field="public_id", queryset=Offering.objects.all())
    staff_public_id = serializers.SlugRelatedField(source="staff", slug_field="public_id", queryset=StaffProfile.objects.all(), required=False, allow_null=True)
    location_public_id = serializers.SlugRelatedField(source="location", slug_field="public_id", queryset=BusinessLocation.objects.all(), required=False, allow_null=True)

    class Meta:
        model = ServiceSession
        fields = ["public_id", "offering_public_id", "staff_public_id", "location_public_id", "starts_at", "ends_at", "capacity", "status"]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        business = self.context["business"]
        offering = attrs.get("offering", getattr(self.instance, "offering", None))
        staff = attrs.get("staff", getattr(self.instance, "staff", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if not offering or offering.business_id != business.id or offering.offering_type != "service":
            raise serializers.ValidationError({"offering_public_id": "Choose a service from this business."})
        if staff and staff.business_id != business.id:
            raise serializers.ValidationError({"staff_public_id": "Choose staff from this business."})
        if location and location.business_id != business.id:
            raise serializers.ValidationError({"location_public_id": "Choose a location from this business."})
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({"ends_at": "End time must be after start time."})
        return attrs


class BookingSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    offering_public_id = serializers.UUIDField(source="offering.public_id", read_only=True)
    offering_name = serializers.CharField(source="offering.name", read_only=True)
    staff_public_id = serializers.UUIDField(source="staff.public_id", read_only=True, allow_null=True)
    staff_name = serializers.CharField(source="staff.display_name", read_only=True, allow_null=True)
    location_public_id = serializers.UUIDField(source="location.public_id", read_only=True, allow_null=True)
    location_name = serializers.CharField(source="location.name", read_only=True, allow_null=True)
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "public_id", "confirmation_code", "customer", "offering_public_id", "offering_name",
            "staff_public_id", "staff_name", "location_public_id", "location_name", "status", "starts_at", "ends_at", "timezone",
            "resources", "seats", "payment_policy", "payment_status", "customer_notes", "cancelled_at", "reminder_sent_at", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "confirmation_code", "customer", "offering_name", "staff_name", "reminder_sent_at", "created_at", "updated_at"]


class PublicBookingInputSerializer(serializers.Serializer):
    offering_public_id = serializers.UUIDField()
    staff_public_id = serializers.UUIDField(required=False, allow_null=True)
    session_public_id = serializers.UUIDField(required=False, allow_null=True)
    location_public_id = serializers.UUIDField(required=False, allow_null=True)
    resource_public_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=20)
    starts_at = serializers.DateTimeField(required=False)
    ends_at = serializers.DateTimeField(required=False)
    timezone = serializers.CharField(max_length=64, default="Asia/Manila")
    seats = serializers.IntegerField(min_value=1, max_value=50, default=1)
    payment_method = serializers.ChoiceField(choices=["paymongo", "manual"], default="paymongo")
    success_url = serializers.URLField(required=False, allow_blank=True)
    cancel_url = serializers.URLField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    customer_notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    def validate(self, attrs):
        business = self.context["business"]
        offering = Offering.objects.filter(business=business, public_id=attrs.pop("offering_public_id"), offering_type="service", status="published").first()
        if not offering:
            raise serializers.ValidationError({"offering_public_id": "This service is not available."})
        attrs["offering"] = offering
        configured_policy = offering.metadata.get("booking_payment_policy", "none")
        attrs["payment_policy"] = configured_policy if configured_policy in {"none", "deposit", "full"} else "none"
        for field, model, target in (
            ("staff_public_id", StaffProfile, "staff"),
            ("session_public_id", ServiceSession, "session"),
            ("location_public_id", BusinessLocation, "location"),
        ):
            identifier = attrs.pop(field, None)
            if identifier:
                obj = model.objects.filter(public_id=identifier, business=business).first()
                if not obj:
                    raise serializers.ValidationError({field: "This selection is not available."})
                attrs[target] = obj
        resource_ids = attrs.pop("resource_public_ids", [])
        if resource_ids:
            resources = list(
                Resource.objects.filter(
                    public_id__in=resource_ids,
                    business=business,
                    is_active=True,
                    is_bookable=True,
                )
            )
            if len(resources) != len(set(resource_ids)):
                raise serializers.ValidationError({"resource_public_ids": "One or more resources are unavailable."})
            if attrs.get("location") and any(resource.location_id != attrs["location"].id for resource in resources):
                raise serializers.ValidationError({"resource_public_ids": "Resources must belong to the selected location."})
            attrs["resources"] = resources
        if not attrs.get("session"):
            if not attrs.get("starts_at") or not attrs.get("ends_at"):
                raise serializers.ValidationError({"starts_at": "Start and end times are required for appointments."})
            if attrs["ends_at"] <= attrs["starts_at"]:
                raise serializers.ValidationError({"ends_at": "End time must be after start time."})
        if not attrs.get("email", "").strip() and not attrs.get("phone", "").strip():
            raise serializers.ValidationError({"phone": "Provide an email address or phone number."})
        return attrs


class VenueEventSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    location_public_id = serializers.SlugRelatedField(
        source="location",
        slug_field="public_id",
        queryset=BusinessLocation.objects.all(),
        required=False,
        allow_null=True,
    )
    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
        allow_null=True,
    )
    layout_public_id = serializers.SlugRelatedField(
        source="layout",
        slug_field="public_id",
        queryset=ResourceLayout.objects.all(),
        required=False,
        allow_null=True,
    )
    layout_name = serializers.CharField(
        source="layout.name",
        read_only=True,
        allow_null=True,
    )
    handler_public_id = serializers.SlugRelatedField(
        source="handler",
        slug_field="public_id",
        queryset=StaffProfile.objects.all(),
        required=False,
        allow_null=True,
    )
    handler_name = serializers.CharField(
        source="handler.display_name",
        read_only=True,
        allow_null=True,
    )
    handler_job_title = serializers.CharField(
        source="handler.job_title",
        read_only=True,
        allow_null=True,
    )
    handler_profile_image_url = serializers.SerializerMethodField()
    assigned_staff_public_ids = serializers.SlugRelatedField(
        source="assigned_staff",
        slug_field="public_id",
        queryset=StaffProfile.objects.all(),
        many=True,
        required=False,
    )
    assigned_staff_summaries = serializers.SerializerMethodField()
    product_public_ids = serializers.SlugRelatedField(
        source="products",
        slug_field="public_id",
        queryset=Offering.objects.all(),
        many=True,
        required=False,
    )
    product_summaries = serializers.SerializerMethodField()
    guest_counts = serializers.SerializerMethodField()

    class Meta:
        model = VenueEvent
        fields = [
            "public_id",
            "title",
            "thumbnail",
            "thumbnail_url",
            "event_type",
            "status",
            "starts_at",
            "ends_at",
            "timezone",
            "location_public_id",
            "location_name",
            "layout_public_id",
            "layout_name",
            "handler_public_id",
            "handler_name",
            "handler_job_title",
            "handler_profile_image_url",
            "assigned_staff_public_ids",
            "assigned_staff_summaries",
            "product_public_ids",
            "product_summaries",
            "organizer_name",
            "organizer_email",
            "organizer_phone",
            "description",
            "max_guests",
            "public_rsvp_enabled",
            "website_enabled",
            "website_template",
            "website_published_at",
            "guest_counts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "public_id",
            "thumbnail_url",
            "handler_name",
            "handler_job_title",
            "handler_profile_image_url",
            "assigned_staff_summaries",
            "product_summaries",
            "guest_counts",
            "website_published_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"thumbnail": {"write_only": True}}

    def get_thumbnail_url(self, obj):
        image = obj.thumbnail or obj.business.cover_image
        if not image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.url) if request else image.url

    def get_handler_profile_image_url(self, obj):
        if not obj.handler or not obj.handler.profile_image:
            return None
        request = self.context.get("request")
        url = obj.handler.profile_image.url
        return request.build_absolute_uri(url) if request else url

    def get_assigned_staff_summaries(self, obj):
        request = self.context.get("request")
        summaries = []
        for member in obj.assigned_staff.all():
            image_url = member.profile_image.url if member.profile_image else None
            if image_url and request:
                image_url = request.build_absolute_uri(image_url)
            summaries.append(
                {
                    "public_id": str(member.public_id),
                    "display_name": member.display_name,
                    "job_title": member.job_title,
                    "profile_image_url": image_url,
                }
            )
        return summaries

    def get_product_summaries(self, obj):
        request = self.context.get("request")
        summaries = []
        for product in obj.products.all():
            image_url = None
            ordered_media = list(product.ordered_media.all())
            preferred_media = next(
                (item for item in ordered_media if item.role == "cover"),
                ordered_media[0] if ordered_media else None,
            )
            if preferred_media and preferred_media.asset:
                image_url = preferred_media.asset.file.url
            else:
                image_asset = next(
                    (
                        asset
                        for asset in product.assets.all()
                        if asset.asset_type == "image"
                    ),
                    None,
                )
                if image_asset:
                    image_url = image_asset.file.url
            if image_url and request:
                image_url = request.build_absolute_uri(image_url)
            summaries.append(
                {
                    "public_id": str(product.public_id),
                    "name": product.name,
                    "summary": product.summary,
                    "offering_type": product.offering_type,
                    "status": product.status,
                    "base_price": product.base_price,
                    "image_url": image_url,
                }
            )
        return summaries

    def validate_thumbnail(self, upload):
        if upload is None:
            return None
        if upload.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Choose an event image up to 5 MB.")
        image = getattr(upload, "image", None)
        if image is None or image.format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError("Use a JPG, PNG, or WebP image.")
        if max(image.size) > 4096:
            raise serializers.ValidationError(
                "Use an image no larger than 4096 pixels per side."
            )
        return upload

    def get_guest_counts(self, obj):
        counts = {
            "total": 0,
            "pending": 0,
            "accepted": 0,
            "declined": 0,
            "maybe": 0,
            "attending_people": 0,
        }
        for guest in obj.guests.all():
            counts["total"] += 1
            counts[guest.response] += 1
            if guest.response == "accepted":
                counts["attending_people"] += guest.party_size
        counts["capacity_remaining"] = max(
            0,
            obj.max_guests - counts["attending_people"],
        )
        return counts

    def validate_max_guests(self, value):
        if value < 1 or value > 10000:
            raise serializers.ValidationError(
                "Choose a maximum attendance from 1 to 10,000."
            )
        if self.instance:
            accepted = self.instance.guests.filter(response="accepted").aggregate(
                total=Sum("party_size")
            )["total"] or 0
            if value < accepted:
                raise serializers.ValidationError(
                    f"Maximum attendance cannot be lower than the {accepted} confirmed guests."
                )
        return value

    def validate(self, attrs):
        business = self.context["business"]
        location = attrs.get("location", getattr(self.instance, "location", None))
        layout = attrs.get("layout", getattr(self.instance, "layout", None))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))

        if location and location.business_id != business.id:
            raise serializers.ValidationError(
                {"location_public_id": "Choose a location from this business."}
            )
        if layout and layout.business_id != business.id:
            raise serializers.ValidationError(
                {"layout_public_id": "Choose a layout from this business."}
            )
        if layout and location and layout.location_id != location.id:
            raise serializers.ValidationError(
                {"layout_public_id": "Choose a layout at the selected location."}
            )
        handler = attrs.get("handler", getattr(self.instance, "handler", None))
        if handler and (handler.business_id != business.id or not handler.is_active):
            raise serializers.ValidationError(
                {"handler_public_id": "Choose an active staff member from this business."}
            )
        assigned_staff = attrs.get("assigned_staff")
        if assigned_staff is not None and any(
            member.business_id != business.id or not member.is_active
            for member in assigned_staff
        ):
            raise serializers.ValidationError(
                {"assigned_staff_public_ids": "Choose active staff members from this business."}
            )
        products = attrs.get("products")
        if products is not None and any(
            product.business_id != business.id or product.status == "archived"
            for product in products
        ):
            raise serializers.ValidationError(
                {"product_public_ids": "Choose available catalog items from this business."}
            )
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End time must be after start time."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        self._include_primary_handler(instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._include_primary_handler(instance)
        return instance

    @staticmethod
    def _include_primary_handler(instance):
        if instance.handler_id:
            instance.assigned_staff.add(instance.handler_id)


class EventGuestSerializer(serializers.ModelSerializer):
    table_public_id = serializers.SlugRelatedField(
        source="table",
        slug_field="public_id",
        queryset=Resource.objects.all(),
        required=False,
        allow_null=True,
    )
    table_name = serializers.CharField(
        source="table.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = EventGuest
        fields = [
            "public_id",
            "full_name",
            "email",
            "phone",
            "party_size",
            "response",
            "table_public_id",
            "table_name",
            "dietary_notes",
            "guest_message",
            "wish_approved",
            "invite_sent_at",
            "responded_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "public_id",
            "invite_sent_at",
            "responded_at",
            "created_at",
            "updated_at",
        ]

    def validate_party_size(self, value):
        if value < 1 or value > 50:
            raise serializers.ValidationError("Choose a party size from 1 to 50.")
        return value

    def validate(self, attrs):
        event = self.context["event"]
        table = attrs.get("table", getattr(self.instance, "table", None))
        if table:
            if table.business_id != event.business_id:
                raise serializers.ValidationError(
                    {"table_public_id": "Choose a table from this event's business."}
                )
            if not event.layout_id or table.layout_id != event.layout_id:
                raise serializers.ValidationError(
                    {"table_public_id": "Choose a table from this event's venue layout."}
                )
            if table.element_type not in {"table", "booth"}:
                raise serializers.ValidationError(
                    {"table_public_id": "Guests can only be assigned to seating elements."}
                )
        if not attrs.get("email", getattr(self.instance, "email", "")).strip() and not attrs.get(
            "phone", getattr(self.instance, "phone", "")
        ).strip():
            raise serializers.ValidationError(
                {"email": "Provide an email address or phone number for the invitation."}
            )
        response = attrs.get(
            "response",
            getattr(self.instance, "response", "pending"),
        )
        party_size = attrs.get(
            "party_size",
            getattr(self.instance, "party_size", 1),
        )
        if response == "accepted":
            accepted_guests = event.guests.filter(response="accepted")
            if self.instance:
                accepted_guests = accepted_guests.exclude(pk=self.instance.pk)
            accepted_people = accepted_guests.aggregate(total=Sum("party_size"))["total"] or 0
            if accepted_people + party_size > event.max_guests:
                raise serializers.ValidationError(
                    {
                        "party_size": (
                            f"Only {max(0, event.max_guests - accepted_people)} "
                            "event places remain."
                        )
                    }
                )
        return attrs


class EventParticipantSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(required=False)
    image_public_id = serializers.SlugRelatedField(
        source="image",
        slug_field="public_id",
        queryset=EventMedia.objects.all(),
        required=False,
        allow_null=True,
    )
    image_url = serializers.SerializerMethodField()
    image_alt_text = serializers.SerializerMethodField()

    class Meta:
        model = EventParticipant
        fields = [
            "public_id",
            "name",
            "role",
            "subtitle",
            "family_text",
            "image_public_id",
            "image_url",
            "image_alt_text",
            "sort_order",
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.image.url) if request else obj.image.image.url

    def get_image_alt_text(self, obj):
        return obj.image.alt_text if obj.image else ""


class EventScheduleSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(required=False)

    class Meta:
        model = EventSchedule
        fields = [
            "public_id",
            "title",
            "starts_at",
            "ends_at",
            "end_time_label",
            "venue_name",
            "address",
            "latitude",
            "longitude",
            "map_url",
            "sort_order",
        ]

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End time must be after start time."}
            )
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Latitude and longitude must be provided together."
            )
        return attrs


class EventStoryBlockSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(required=False)
    image_public_id = serializers.SlugRelatedField(
        source="image",
        slug_field="public_id",
        queryset=EventMedia.objects.all(),
        required=False,
        allow_null=True,
    )
    image_url = serializers.SerializerMethodField()
    image_alt_text = serializers.SerializerMethodField()

    class Meta:
        model = EventStoryBlock
        fields = [
            "public_id",
            "title",
            "body",
            "date_label",
            "image_public_id",
            "image_url",
            "image_alt_text",
            "sort_order",
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.image.url) if request else obj.image.image.url

    def get_image_alt_text(self, obj):
        return obj.image.alt_text if obj.image else ""


class EventQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventQuote
        fields = [
            "is_enabled",
            "original_text",
            "translation",
            "citation",
        ]


class EventMediaSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = EventMedia
        fields = [
            "public_id",
            "image",
            "image_url",
            "placement",
            "caption",
            "alt_text",
            "sort_order",
            "is_featured",
        ]
        read_only_fields = ["public_id", "image_url"]
        extra_kwargs = {"image": {"write_only": True}}

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

    def validate_image(self, upload):
        if upload.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Choose an event image up to 10 MB.")
        image = getattr(upload, "image", None)
        if image is None or image.format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError("Use a JPG, PNG, or WebP image.")
        if max(image.size) > 6000:
            raise serializers.ValidationError(
                "Use an image no larger than 6000 pixels per side."
            )
        return upload


class EventMusicUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    ALLOWED_EXTENSIONS = {".mp3", ".m4a", ".ogg", ".wav", ".webm"}

    def validate_file(self, upload):
        if upload.size > 15 * 1024 * 1024:
            raise serializers.ValidationError("Choose an audio file up to 15 MB.")

        extension = Path(upload.name).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("Use an MP3, M4A, OGG, WAV, or WebM audio file.")

        header = upload.read(16)
        upload.seek(0)
        has_valid_signature = (
            header.startswith(b"ID3")
            or header[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}
            or (header.startswith(b"RIFF") and header[8:12] == b"WAVE")
            or header.startswith(b"OggS")
            or header.startswith(b"\x1aE\xdf\xa3")
            or header[4:8] == b"ftyp"
        )
        if not has_valid_signature:
            raise serializers.ValidationError("The uploaded file is not recognized as supported audio.")
        return upload


class VenueEventWebsiteSerializer(serializers.ModelSerializer):
    participants = EventParticipantSerializer(many=True, required=False)
    schedule_entries = EventScheduleSerializer(many=True, required=False)
    story_blocks = EventStoryBlockSerializer(many=True, required=False)
    quote = EventQuoteSerializer(required=False, allow_null=True)
    media = EventMediaSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    approved_wishes = serializers.SerializerMethodField()
    background_music_url = serializers.SerializerMethodField()

    FONT_CHOICES = {
        "Bodoni Moda",
        "Cormorant Garamond",
        "Newsreader",
        "Italiana",
        "Manrope",
        "Montserrat",
    }
    SECTION_KEYS = {
        "event_detail",
        "participants",
        "story",
        "quote",
        "wish",
        "gallery",
    }
    DEFAULT_SECTION_ORDER = [
        "hero",
        "event_detail",
        "participants",
        "story",
        "quote",
        "wish",
        "gallery",
    ]
    RSVP_DEFAULTS = {
        "heading": "RSVP",
        "subtitle": "Will you celebrate with us?",
        "deadline": None,
        "submit_label": "Send RSVP",
        "accept_label": "Joyfully accept",
        "decline_label": "Regretfully decline",
        "allow_maybe": False,
        "show_party_size": True,
        "show_dietary_notes": True,
        "show_guest_message": True,
        "max_party_size": 10,
        "attending_title": "Thank you",
        "attending_message": "We are so happy you will celebrate with us.",
        "declining_title": "Thank you for letting us know",
        "declining_message": "We will be thinking of you on our special day.",
    }
    DRESS_CODE_DEFAULTS = {
        "enabled": False,
        "heading": "Dress code",
        "subtitle": "Color palette and style",
        "description": "",
        "colors": [],
        "media_public_id": None,
    }
    EVENT_NOTES_DEFAULTS = {
        "enabled": False,
        "heading": "Details",
        "subtitle": "A few thoughtful notes",
        "items": [],
    }
    RSVP_KEYS = set(RSVP_DEFAULTS)
    DRESS_CODE_KEYS = set(DRESS_CODE_DEFAULTS) | {"media_url"}
    EVENT_NOTES_KEYS = set(EVENT_NOTES_DEFAULTS)
    EVENT_NOTE_KEYS = {"icon", "title", "body"}
    EVENT_NOTE_ICONS = {
        "calendar",
        "car",
        "gift",
        "heart",
        "hotel",
        "info",
        "sparkles",
        "utensils",
    }
    TEMPLATE_GROUPS = {
        "wedding": {
            "wedding_editorial",
            "wedding_garden",
            "wedding_modern",
        },
        "birthday": {
            "birthday_color",
            "birthday_after_dark",
            "birthday_milestone",
        },
        "general": {
            "general_spotlight",
            "general_studio",
            "general_community",
        },
    }

    class Meta:
        model = VenueEvent
        fields = [
            "public_id",
            "title",
            "event_type",
            "starts_at",
            "ends_at",
            "timezone",
            "description",
            "max_guests",
            "public_rsvp_enabled",
            "website_enabled",
            "website_template",
            "invitation_text",
            "closing_message",
            "hero_date_text",
            "header_mark_type",
            "header_mark_text",
            "wish_display_mode",
            "countdown_enabled",
            "countdown_label",
            "theme_background",
            "theme_text",
            "theme_accent",
            "heading_font",
            "body_font",
            "sections_config",
            "popup_enabled",
            "popup_title",
            "popup_message",
            "popup_button_label",
            "music_enabled",
            "background_music_url",
            "background_music_title",
            "music_volume",
            "website_published_at",
            "thumbnail_url",
            "participants",
            "schedule_entries",
            "story_blocks",
            "quote",
            "media",
            "approved_wishes",
        ]
        read_only_fields = [
            "public_id",
            "starts_at",
            "ends_at",
            "timezone",
            "max_guests",
            "public_rsvp_enabled",
            "website_published_at",
            "thumbnail_url",
            "media",
            "approved_wishes",
            "background_music_url",
        ]

    def get_thumbnail_url(self, obj):
        image = obj.thumbnail or obj.business.cover_image
        if not image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.url) if request else image.url

    def get_approved_wishes(self, obj):
        if (
            self.context.get("public")
            and obj.wish_display_mode == "event_day"
            and timezone.now() < obj.starts_at
        ):
            return []
        return [
            {"name": guest.full_name, "message": guest.guest_message}
            for guest in obj.guests.all()
            if guest.wish_approved and guest.guest_message.strip()
        ]

    def get_background_music_url(self, obj):
        if not obj.background_music:
            return None
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.background_music.url)
            if request
            else obj.background_music.url
        )

    def validate_sections_config(self, sections):
        if not isinstance(sections, dict):
            raise serializers.ValidationError("Section settings must be an object.")

        allowed_keys = self.SECTION_KEYS | {
            "order",
            "rsvp",
            "dress_code",
            "event_notes",
        }
        if set(sections) - allowed_keys:
            raise serializers.ValidationError("Unsupported event section setting.")

        normalized = {
            key: sections.get(key, True)
            for key in self.SECTION_KEYS
        }
        for key in self.SECTION_KEYS:
            if not isinstance(normalized[key], bool):
                raise serializers.ValidationError(
                    f"{key.replace('_', ' ').title()} visibility must be true or false."
                )

        order = sections.get("order", self.DEFAULT_SECTION_ORDER)
        allowed_order = self.SECTION_KEYS | {"hero"}
        if (
            not isinstance(order, list)
            or any(item not in allowed_order for item in order)
            or len(order) != len(set(order))
        ):
            raise serializers.ValidationError(
                "Section order contains an unsupported or repeated value."
            )
        normalized["order"] = list(order)
        normalized["rsvp"] = self._validate_rsvp_config(sections.get("rsvp", {}))
        normalized["dress_code"] = self._validate_dress_code_config(
            sections.get("dress_code", {})
        )
        normalized["event_notes"] = self._validate_event_notes_config(
            sections.get("event_notes", {})
        )
        return normalized

    def _validate_rsvp_config(self, value):
        if not isinstance(value, dict) or set(value) - self.RSVP_KEYS:
            raise serializers.ValidationError("RSVP settings contain an unsupported value.")
        config = {**self.RSVP_DEFAULTS, **value}
        text_limits = {
            "heading": 80,
            "subtitle": 180,
            "submit_label": 50,
            "accept_label": 60,
            "decline_label": 60,
            "attending_title": 100,
            "attending_message": 500,
            "declining_title": 100,
            "declining_message": 500,
        }
        for key, limit in text_limits.items():
            config[key] = serializers.CharField(
                max_length=limit,
                allow_blank=False,
                trim_whitespace=True,
            ).run_validation(config[key])
        for key in (
            "allow_maybe",
            "show_party_size",
            "show_dietary_notes",
            "show_guest_message",
        ):
            config[key] = serializers.BooleanField().run_validation(config[key])
        config["max_party_size"] = serializers.IntegerField(
            min_value=1,
            max_value=50,
        ).run_validation(config["max_party_size"])
        deadline = serializers.DateTimeField(allow_null=True).run_validation(
            config["deadline"]
        )
        config["deadline"] = deadline.isoformat() if deadline else None
        return config

    def _validate_dress_code_config(self, value):
        if not isinstance(value, dict) or set(value) - self.DRESS_CODE_KEYS:
            raise serializers.ValidationError(
                "Dress-code settings contain an unsupported value."
            )
        config = {**self.DRESS_CODE_DEFAULTS, **value}
        config.pop("media_url", None)
        config["enabled"] = serializers.BooleanField().run_validation(config["enabled"])
        for key, limit, allow_blank in (
            ("heading", 80, False),
            ("subtitle", 180, True),
            ("description", 1200, True),
        ):
            config[key] = serializers.CharField(
                max_length=limit,
                allow_blank=allow_blank,
                trim_whitespace=True,
            ).run_validation(config[key])

        colors = config["colors"]
        if not isinstance(colors, list) or len(colors) > 8:
            raise serializers.ValidationError("Choose up to eight dress-code colors.")
        for color in colors:
            if not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                raise serializers.ValidationError(
                    "Dress-code colors must use six-digit hexadecimal values."
                )
        config["colors"] = [color.upper() for color in colors]

        media_public_id = config["media_public_id"]
        if media_public_id:
            media_public_id = serializers.UUIDField().run_validation(media_public_id)
            if not EventMedia.objects.filter(
                event=self.instance,
                public_id=media_public_id,
            ).exists():
                raise serializers.ValidationError(
                    "Choose a dress-code image from this event."
                )
            config["media_public_id"] = str(media_public_id)
        else:
            config["media_public_id"] = None
        return config

    def _validate_event_notes_config(self, value):
        if not isinstance(value, dict) or set(value) - self.EVENT_NOTES_KEYS:
            raise serializers.ValidationError(
                "Event-note settings contain an unsupported value."
            )
        config = {**self.EVENT_NOTES_DEFAULTS, **value}
        config["enabled"] = serializers.BooleanField().run_validation(config["enabled"])
        config["heading"] = serializers.CharField(
            max_length=80,
            allow_blank=False,
            trim_whitespace=True,
        ).run_validation(config["heading"])
        config["subtitle"] = serializers.CharField(
            max_length=180,
            allow_blank=True,
            trim_whitespace=True,
        ).run_validation(config["subtitle"])
        items = config["items"]
        if not isinstance(items, list) or len(items) > 8:
            raise serializers.ValidationError("Add up to eight event notes.")

        normalized_items = []
        for item in items:
            if not isinstance(item, dict) or set(item) - self.EVENT_NOTE_KEYS:
                raise serializers.ValidationError("An event note contains an unsupported value.")
            icon = serializers.ChoiceField(choices=sorted(self.EVENT_NOTE_ICONS)).run_validation(
                item.get("icon", "info")
            )
            title = serializers.CharField(
                max_length=100,
                allow_blank=False,
                trim_whitespace=True,
            ).run_validation(item.get("title", ""))
            body = serializers.CharField(
                max_length=800,
                allow_blank=True,
                trim_whitespace=True,
            ).run_validation(item.get("body", ""))
            normalized_items.append({"icon": icon, "title": title, "body": body})
        config["items"] = normalized_items
        return config

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        sections = self.validate_sections_config(representation.get("sections_config") or {})
        dress_code = sections["dress_code"]
        dress_code["media_url"] = None
        if dress_code["media_public_id"]:
            media = instance.media.filter(
                public_id=dress_code["media_public_id"]
            ).first()
            if media:
                request = self.context.get("request")
                dress_code["media_url"] = (
                    request.build_absolute_uri(media.image.url)
                    if request
                    else media.image.url
                )
        representation["sections_config"] = sections
        return representation

    def validate(self, attrs):
        for field in ("theme_background", "theme_text", "theme_accent"):
            value = attrs.get(field, getattr(self.instance, field, ""))
            if value and not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
                raise serializers.ValidationError(
                    {field: "Use a six-digit hexadecimal color such as #000000."}
                )
        for field in ("heading_font", "body_font"):
            value = attrs.get(field, getattr(self.instance, field, ""))
            if value not in self.FONT_CHOICES:
                raise serializers.ValidationError(
                    {field: "Choose one of the supported event fonts."}
                )
        if "event_type" in attrs or "website_template" in attrs:
            event_type = attrs.get("event_type", self.instance.event_type)
            template = attrs.get("website_template", self.instance.website_template)
            group = (
                event_type
                if event_type in {"wedding", "birthday"}
                else "general"
            )
            if template not in self.TEMPLATE_GROUPS[group]:
                raise serializers.ValidationError(
                    {"website_template": "Choose a template designed for this event type."}
                )

        for story in attrs.get("story_blocks", []):
            image = story.get("image")
            if image and image.event_id != self.instance.id:
                raise serializers.ValidationError(
                    {"story_blocks": "Choose story images from this event only."}
                )

        for participant in attrs.get("participants", []):
            image = participant.get("image")
            if image and image.event_id != self.instance.id:
                raise serializers.ValidationError(
                    {"participants": "Choose participant portraits from this event only."}
                )

        music_enabled = attrs.get(
            "music_enabled",
            getattr(self.instance, "music_enabled", False),
        )
        has_music = bool(getattr(self.instance, "background_music", None))
        if music_enabled and not has_music:
            raise serializers.ValidationError(
                {"music_enabled": "Upload background audio before enabling music."}
            )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        participants = validated_data.pop("participants", None)
        schedules = validated_data.pop("schedule_entries", None)
        story_blocks = validated_data.pop("story_blocks", None)
        quote = validated_data.pop("quote", None)
        instance = super().update(instance, validated_data)

        if participants is not None:
            self.sync_related(instance, "participants", EventParticipant, participants)
        if schedules is not None:
            self.sync_related(instance, "schedule_entries", EventSchedule, schedules)
        if story_blocks is not None:
            self.sync_related(instance, "story_blocks", EventStoryBlock, story_blocks)
        if quote is not None:
            EventQuote.objects.update_or_create(event=instance, defaults=quote)
        return instance

    @staticmethod
    def sync_related(event, relation_name, model, items):
        manager = getattr(event, relation_name)
        current = {str(item.public_id): item for item in manager.all()}
        retained_ids = []
        for values in items:
            public_id = values.pop("public_id", None)
            record = current.get(str(public_id)) if public_id else None
            if record:
                for field, value in values.items():
                    setattr(record, field, value)
                record.save(update_fields=[*values.keys()])
            else:
                record = model.objects.create(event=event, **values)
            retained_ids.append(record.pk)
        manager.exclude(pk__in=retained_ids).delete()


class PublicRsvpSerializer(serializers.Serializer):
    response = serializers.ChoiceField(choices=["accepted", "declined", "maybe"])
    party_size = serializers.IntegerField(min_value=1, max_value=50)
    dietary_notes = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
    )
    guest_message = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        event = self.context["event"]
        guest = self.context["guest"]
        sections = event.sections_config if isinstance(event.sections_config, dict) else {}
        rsvp = sections.get("rsvp") if isinstance(sections.get("rsvp"), dict) else {}
        if (
            attrs["response"] == "maybe"
            and not rsvp.get("allow_maybe", False)
            and guest.response != "maybe"
        ):
            raise serializers.ValidationError(
                {"response": "Maybe is not available for this invitation."}
            )
        if attrs["response"] != "accepted":
            return attrs
        try:
            configured_party_size = int(rsvp.get("max_party_size", 10))
        except (TypeError, ValueError):
            configured_party_size = 10
        max_party_size = (
            min(max(configured_party_size, 1), 50)
            if rsvp.get("show_party_size", True)
            else 50
        )
        if attrs["party_size"] > max_party_size:
            raise serializers.ValidationError(
                {
                    "party_size": (
                        f"This invitation allows up to {max_party_size} people."
                    )
                }
            )
        accepted_people = event.guests.filter(response="accepted").exclude(
            pk=guest.pk
        ).aggregate(total=Sum("party_size"))["total"] or 0
        if accepted_people + attrs["party_size"] > event.max_guests:
            raise serializers.ValidationError(
                {
                    "party_size": (
                        f"Only {max(0, event.max_guests - accepted_people)} "
                        "event places remain."
                    )
                }
            )
        return attrs


class EventInviteActionSerializer(serializers.Serializer):
    regenerate = serializers.BooleanField(default=False)
    send_email = serializers.BooleanField(default=False)
