import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from businesses.models import Business, BusinessEvent, BusinessLocation, BusinessMembership
from catalog.models import Offering
from commerce.models import Customer, Order


def staff_code():
    return f"PC-{uuid.uuid4().hex[:8].upper()}"


def booking_confirmation_code():
    return f"BK-{uuid.uuid4().hex[:8].upper()}"


def staff_profile_image_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return (
        f"businesses/{instance.business.public_id}/workforce/"
        f"{instance.public_id}/profile/{uuid.uuid4().hex}{extension}"
    )


def venue_event_thumbnail_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return (
        f"businesses/{instance.business.public_id}/events/"
        f"{instance.public_id}/thumbnail/{uuid.uuid4().hex}{extension}"
    )


def venue_event_media_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return (
        f"businesses/{instance.event.business.public_id}/events/"
        f"{instance.event.public_id}/media/{instance.public_id}/{uuid.uuid4().hex}{extension}"
    )


def venue_event_music_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return (
        f"businesses/{instance.business.public_id}/events/"
        f"{instance.public_id}/music/{uuid.uuid4().hex}{extension}"
    )


def default_event_sections():
    return {
        "event_detail": True,
        "participants": True,
        "story": True,
        "quote": True,
        "wish": True,
        "gallery": True,
        "order": [
            "hero",
            "event_detail",
            "participants",
            "story",
            "quote",
            "wish",
            "gallery",
        ],
    }


class StaffProfile(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="staff_profiles")
    membership = models.OneToOneField(BusinessMembership, on_delete=models.SET_NULL, blank=True, null=True, related_name="staff_profile")
    display_name = models.CharField(max_length=160)
    profile_image = models.ImageField(
        upload_to=staff_profile_image_path,
        max_length=500,
        blank=True,
        null=True,
    )
    email = models.EmailField(blank=True)
    employee_code = models.CharField(max_length=16, unique=True, default=staff_code, editable=False)
    job_title = models.CharField(max_length=120, blank=True)
    employment_status = models.CharField(max_length=16, choices=[("pending", "Pending"), ("active", "Active"), ("suspended", "Suspended"), ("inactive", "Inactive")], default="active")
    hired_at = models.DateField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=160, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, blank=True)
    scheduled_start_time = models.TimeField(blank=True, null=True)
    scheduled_end_time = models.TimeField(blank=True, null=True)
    late_grace_minutes = models.PositiveSmallIntegerField(default=10)
    consecutive_late_threshold = models.PositiveSmallIntegerField(default=3)
    attendance_pin_digest = models.CharField(max_length=64, blank=True, db_index=True)
    attendance_pin_generated_at = models.DateTimeField(blank=True, null=True)
    bio = models.TextField(blank=True, max_length=2000)
    timezone = models.CharField(max_length=64, default="Asia/Manila")
    is_bookable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]


class AvailabilityRule(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="availability_rules")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="availability_rules")
    location = models.ForeignKey(BusinessLocation, on_delete=models.CASCADE, blank=True, null=True, related_name="availability_rules")
    weekday = models.PositiveSmallIntegerField()
    starts_at = models.TimeField()
    ends_at = models.TimeField()
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday", "starts_at"]


class AvailabilityException(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="availability_exceptions")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="availability_exceptions")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    exception_type = models.CharField(max_length=16, choices=[("unavailable", "Unavailable"), ("available", "Available"), ("break", "Break")], default="unavailable")
    reason = models.CharField(max_length=200, blank=True)


class ServiceAssignment(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="service_assignments")
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name="service_assignments")
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="staff_assignments")
    location = models.ForeignKey(BusinessLocation, on_delete=models.CASCADE, blank=True, null=True, related_name="service_assignments")
    price_override = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    duration_override = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["staff", "offering", "location"], name="unique_staff_service_location")]


class ServiceSession(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="service_sessions")
    offering = models.ForeignKey(Offering, on_delete=models.PROTECT, related_name="sessions")
    staff = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, blank=True, null=True, related_name="sessions")
    location = models.ForeignKey(BusinessLocation, on_delete=models.SET_NULL, blank=True, null=True, related_name="service_sessions")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=[("scheduled", "Scheduled"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="scheduled")

    class Meta:
        ordering = ["starts_at"]


class ResourceType(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="resource_types")
    name = models.CharField(max_length=100)
    singular_label = models.CharField(max_length=80)
    plural_label = models.CharField(max_length=80)
    icon = models.CharField(max_length=40, default="layout-grid")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_resource_type")]
        ordering = ["name"]


class ResourceLayout(models.Model):
    LAYOUT_TYPES = [
        ("restaurant", "Restaurant dining"),
        ("event", "Event or wedding"),
        ("room", "Room or studio"),
        ("general", "General venue"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="resource_layouts")
    location = models.ForeignKey(BusinessLocation, on_delete=models.CASCADE, related_name="resource_layouts")
    name = models.CharField(max_length=120)
    layout_type = models.CharField(max_length=24, choices=LAYOUT_TYPES, default="general")
    description = models.CharField(max_length=240, blank=True)
    width = models.PositiveSmallIntegerField(default=100)
    height = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["location", "name"], name="unique_location_resource_layout")]
        ordering = ["name"]


class Resource(models.Model):
    SHAPES = [("round", "Round"), ("square", "Square"), ("rectangle", "Rectangle")]
    ELEMENT_TYPES = [
        ("table", "Table or seating"),
        ("stage", "Stage"),
        ("dance_floor", "Dance floor"),
        ("bar", "Bar"),
        ("buffet", "Buffet or service station"),
        ("entrance", "Entrance"),
        ("booth", "Booth or exhibit"),
        ("service", "Service area"),
        ("decor", "Decor or landmark"),
        ("other", "Other"),
    ]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.ForeignKey(ResourceType, on_delete=models.PROTECT, related_name="resources")
    location = models.ForeignKey(BusinessLocation, on_delete=models.CASCADE, related_name="resources")
    layout = models.ForeignKey(ResourceLayout, on_delete=models.SET_NULL, blank=True, null=True, related_name="resources")
    name = models.CharField(max_length=100)
    element_type = models.CharField(max_length=24, choices=ELEMENT_TYPES, default="other")
    is_bookable = models.BooleanField(default=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    shape = models.CharField(max_length=16, choices=SHAPES, default="square")
    width = models.PositiveSmallIntegerField(default=16)
    height = models.PositiveSmallIntegerField(default=16)
    rotation = models.SmallIntegerField(default=0)
    position_x = models.PositiveSmallIntegerField(default=20)
    position_y = models.PositiveSmallIntegerField(default=20)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["location", "name"], name="unique_location_resource_name")]
        ordering = ["name"]


class SchedulingSettings(models.Model):
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name="scheduling_settings",
    )
    public_booking_enabled = models.BooleanField(default=True)
    public_intro = models.CharField(max_length=280, blank=True)
    advance_booking_days = models.PositiveSmallIntegerField(default=31)
    updated_at = models.DateTimeField(auto_now=True)


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"),
        ("completed", "Completed"), ("no_show", "No show"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    confirmation_code = models.CharField(
        max_length=16,
        unique=True,
        default=booking_confirmation_code,
        editable=False,
    )
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="bookings")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bookings")
    offering = models.ForeignKey(Offering, on_delete=models.PROTECT, related_name="bookings")
    staff = models.ForeignKey(StaffProfile, on_delete=models.PROTECT, blank=True, null=True, related_name="bookings")
    location = models.ForeignKey(BusinessLocation, on_delete=models.PROTECT, blank=True, null=True, related_name="bookings")
    resources = models.ManyToManyField(Resource, through="BookingResource", related_name="bookings", blank=True)
    session = models.ForeignKey(ServiceSession, on_delete=models.PROTECT, blank=True, null=True, related_name="bookings")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True, related_name="bookings")
    event = models.OneToOneField(BusinessEvent, on_delete=models.SET_NULL, blank=True, null=True, related_name="booking")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    timezone = models.CharField(max_length=64, default="Asia/Manila")
    seats = models.PositiveIntegerField(default=1)
    payment_policy = models.CharField(max_length=16, choices=[("none", "No payment"), ("deposit", "Deposit"), ("full", "Full payment")], default="none")
    payment_status = models.CharField(max_length=16, choices=[("not_required", "Not required"), ("unpaid", "Unpaid"), ("paid", "Paid")], default="not_required")
    customer_notes = models.TextField(blank=True, max_length=2000)
    cancellation_token_digest = models.CharField(max_length=64)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "id"]


class BookingResource(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="resource_allocations")
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name="booking_allocations")
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["booking", "resource"], name="unique_booking_resource")]


class VenueEvent(models.Model):
    EVENT_TYPES = [
        ("wedding", "Wedding"),
        ("birthday", "Birthday"),
        ("general", "General event"),
        ("private_event", "Private event"),
        ("corporate", "Corporate event"),
        ("community", "Community event"),
        ("other", "Other event"),
    ]
    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("open", "RSVP open"),
        ("closed", "RSVP closed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="venue_events",
    )
    title = models.CharField(max_length=180)
    thumbnail = models.ImageField(
        upload_to=venue_event_thumbnail_path,
        max_length=500,
        blank=True,
        null=True,
    )
    event_type = models.CharField(
        max_length=24,
        choices=EVENT_TYPES,
        default="private_event",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="planning",
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    timezone = models.CharField(max_length=64, default="Asia/Manila")
    location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="venue_events",
    )
    layout = models.ForeignKey(
        ResourceLayout,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="venue_events",
    )
    handler = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="handled_venue_events",
    )
    assigned_staff = models.ManyToManyField(
        StaffProfile,
        blank=True,
        related_name="assigned_venue_events",
    )
    products = models.ManyToManyField(
        Offering,
        blank=True,
        related_name="venue_events",
    )
    calendar_event = models.OneToOneField(
        BusinessEvent,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="venue_event",
    )
    organizer_name = models.CharField(max_length=160)
    organizer_email = models.EmailField(blank=True)
    organizer_phone = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True, max_length=4000)
    max_guests = models.PositiveIntegerField(default=100)
    public_rsvp_enabled = models.BooleanField(default=True)
    website_enabled = models.BooleanField(default=False)
    website_template = models.CharField(
        max_length=32,
        choices=[
            ("wedding_editorial", "Editorial noir"),
            ("wedding_garden", "Garden vow"),
            ("wedding_modern", "Modern ceremony"),
            ("birthday_color", "Color story"),
            ("birthday_after_dark", "After dark"),
            ("birthday_milestone", "Milestone portrait"),
            ("general_spotlight", "Event spotlight"),
            ("general_studio", "Studio programme"),
            ("general_community", "Community canvas"),
        ],
        default="wedding_editorial",
    )
    invitation_text = models.CharField(
        max_length=500,
        blank=True,
        default="You are invited to celebrate with us.",
    )
    closing_message = models.CharField(max_length=180, blank=True, default="With love")
    hero_date_text = models.CharField(max_length=32, blank=True)
    header_mark_type = models.CharField(
        max_length=8,
        choices=[("text", "Text"), ("logo", "Business logo")],
        default="text",
    )
    header_mark_text = models.CharField(max_length=120, blank=True)
    wish_display_mode = models.CharField(
        max_length=16,
        choices=[
            ("realtime", "Show as approved"),
            ("event_day", "Reveal on event day"),
        ],
        default="realtime",
    )
    countdown_enabled = models.BooleanField(default=False)
    countdown_label = models.CharField(
        max_length=80,
        blank=True,
        default="Until we celebrate",
    )
    theme_background = models.CharField(max_length=7, default="#000000")
    theme_text = models.CharField(max_length=7, default="#F5F3EE")
    theme_accent = models.CharField(max_length=7, default="#D6D1C8")
    heading_font = models.CharField(max_length=48, default="Bodoni Moda")
    body_font = models.CharField(max_length=48, default="Manrope")
    sections_config = models.JSONField(default=default_event_sections, blank=True)
    popup_enabled = models.BooleanField(default=False)
    popup_title = models.CharField(max_length=120, blank=True)
    popup_message = models.CharField(max_length=500, blank=True)
    popup_button_label = models.CharField(
        max_length=50,
        blank=True,
        default="Enter event",
    )
    music_enabled = models.BooleanField(default=False)
    background_music = models.FileField(
        upload_to=venue_event_music_path,
        max_length=500,
        blank=True,
        null=True,
    )
    background_music_title = models.CharField(max_length=120, blank=True)
    music_volume = models.PositiveSmallIntegerField(
        default=35,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    website_published_at = models.DateTimeField(blank=True, null=True)
    organizer_token_digest = models.CharField(max_length=64, blank=True)
    organizer_token_ciphertext = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_venue_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "id"]

    def __str__(self):
        return self.title


class EventGuest(models.Model):
    RESPONSE_CHOICES = [
        ("pending", "Awaiting reply"),
        ("accepted", "Attending"),
        ("declined", "Not attending"),
        ("maybe", "Maybe"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        VenueEvent,
        on_delete=models.CASCADE,
        related_name="guests",
    )
    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    party_size = models.PositiveSmallIntegerField(default=1)
    response = models.CharField(
        max_length=16,
        choices=RESPONSE_CHOICES,
        default="pending",
    )
    table = models.ForeignKey(
        Resource,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="event_guests",
    )
    dietary_notes = models.CharField(max_length=500, blank=True)
    guest_message = models.CharField(max_length=1000, blank=True)
    wish_approved = models.BooleanField(default=False)
    invite_token_digest = models.CharField(max_length=64, blank=True)
    invite_token_ciphertext = models.TextField(blank=True)
    invite_sent_at = models.DateTimeField(blank=True, null=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return f"{self.full_name} — {self.event.title}"


class EventParticipant(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        VenueEvent,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    name = models.CharField(max_length=160)
    role = models.CharField(max_length=80, blank=True)
    subtitle = models.CharField(max_length=160, blank=True)
    family_text = models.CharField(max_length=500, blank=True)
    image = models.ForeignKey(
        "EventMedia",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="participants",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]


class EventSchedule(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        VenueEvent,
        on_delete=models.CASCADE,
        related_name="schedule_entries",
    )
    title = models.CharField(max_length=120)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    end_time_label = models.CharField(max_length=64, blank=True)
    venue_name = models.CharField(max_length=180)
    address = models.CharField(max_length=500, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    map_url = models.URLField(max_length=500, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "starts_at", "id"]


class EventStoryBlock(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        VenueEvent,
        on_delete=models.CASCADE,
        related_name="story_blocks",
    )
    title = models.CharField(max_length=160, blank=True)
    body = models.TextField(max_length=4000)
    date_label = models.CharField(max_length=80, blank=True)
    image = models.ForeignKey(
        "EventMedia",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="story_blocks",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]


class EventQuote(models.Model):
    event = models.OneToOneField(
        VenueEvent,
        on_delete=models.CASCADE,
        related_name="quote",
    )
    is_enabled = models.BooleanField(default=False)
    original_text = models.TextField(max_length=2000, blank=True)
    translation = models.TextField(max_length=2000, blank=True)
    citation = models.CharField(max_length=240, blank=True)


class EventMedia(models.Model):
    PLACEMENT_CHOICES = [
        ("hero", "Hero"),
        ("popup", "Popup"),
        ("participant", "Participant"),
        ("story", "Story"),
        ("gallery", "Gallery"),
        ("closing", "Closing"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        VenueEvent,
        on_delete=models.CASCADE,
        related_name="media",
    )
    image = models.ImageField(upload_to=venue_event_media_path, max_length=500)
    placement = models.CharField(
        max_length=16,
        choices=PLACEMENT_CHOICES,
        default="gallery",
    )
    caption = models.CharField(max_length=240, blank=True)
    alt_text = models.CharField(max_length=240)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
