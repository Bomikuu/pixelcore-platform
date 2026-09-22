import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


User = get_user_model()


def account_challenge_expiry():
    return timezone.now() + timedelta(minutes=15)


def default_branding():
    from .identity import default_identity_config

    return default_identity_config()


def default_modules():
    return ["site", "sell", "schedule", "operate"]


def business_asset_path(instance, filename):
    return f"businesses/{instance.public_id}/{filename}"


def library_asset_path(instance, filename):
    return f"businesses/{instance.business.public_id}/library/{instance.public_id}/{filename}"


class Business(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("pending", "Pending"),
        ("archived", "Archived"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    industry_preset = models.CharField(
        max_length=24,
        choices=[
            ("general", "General business"),
            ("restaurant", "Restaurant"),
            ("retail", "Retail"),
            ("services", "Services"),
            ("hybrid", "Hybrid"),
        ],
        default="general",
    )
    display_name = models.CharField(max_length=160)
    legal_name = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    industry = models.CharField(max_length=80, blank=True)
    tagline = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True, max_length=4000)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(
        max_length=32,
        blank=True,
        validators=[RegexValidator(r"^[0-9+().\-\s]*$", "Enter a valid phone number.")],
    )
    website_url = models.URLField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=24, blank=True)
    country = models.CharField(max_length=2, default="PH")
    timezone = models.CharField(max_length=64, default="Asia/Manila")
    locale = models.CharField(max_length=16, default="en-PH")
    currency = models.CharField(max_length=3, default="PHP")
    currency_locked_at = models.DateTimeField(blank=True, null=True)
    tax_id = models.CharField(max_length=64, blank=True)
    tax_status = models.CharField(
        max_length=16,
        choices=[("non_vat", "Non-VAT"), ("vat", "VAT-registered"), ("exempt", "Tax exempt")],
        default="non_vat",
    )
    prices_include_tax = models.BooleanField(default=True)
    logo = models.ImageField(upload_to=business_asset_path, blank=True)
    favicon = models.ImageField(upload_to=business_asset_path, blank=True)
    cover_image = models.ImageField(upload_to=business_asset_path, blank=True)
    branding = models.JSONField(default=default_branding)
    enabled_modules = models.JSONField(default=default_modules)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_businesses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.display_name)[:150] or "business"
            candidate = base
            suffix = 2
            while Business.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


class BusinessMembership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("invited", "Invited"),
        ("suspended", "Suspended"),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="business_memberships")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="staff")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "user"],
                name="unique_business_membership",
            )
        ]
        ordering = ["business_id", "user_id"]

    def __str__(self):
        return f"{self.user} at {self.business}"


class BusinessCard(models.Model):
    STYLE_CHOICES = [
        ("signature", "Signature"),
        ("editorial", "Editorial"),
        ("studio", "Studio"),
        ("luxury", "Luxury"),
    ]
    ORIENTATION_CHOICES = [
        ("landscape", "Landscape"),
        ("portrait", "Portrait"),
    ]
    FONT_STYLE_CHOICES = [
        ("modern", "Modern"),
        ("editorial", "Editorial"),
        ("geometric", "Geometric"),
        ("warm", "Warm"),
    ]
    FONT_FAMILY_CHOICES = [
        ("manrope", "Manrope"),
        ("newsreader", "Newsreader"),
        ("playfair", "Playfair Display"),
        ("cormorant", "Cormorant Garamond"),
        ("montserrat", "Montserrat"),
        ("jakarta", "Plus Jakarta Sans"),
        ("great_vibes", "Great Vibes"),
        ("allura", "Allura"),
        ("parisienne", "Parisienne"),
        ("alex_brush", "Alex Brush"),
        ("lobster", "Lobster"),
        ("playball", "Playball"),
        ("custom", "Custom uploaded font"),
    ]
    CUSTOMIZATION_MODE_CHOICES = [
        ("style", "Style default"),
        ("custom", "Custom"),
    ]
    BACKGROUND_TYPE_CHOICES = [
        ("generated", "Generated pattern"),
        ("image", "Image background"),
    ]
    BACKGROUND_APPLY_CHOICES = [
        ("front", "Front only"),
        ("back", "Back only"),
        ("both", "Both sides"),
    ]
    IMAGE_FIT_CHOICES = [
        ("cover", "Cover"),
        ("contain", "Contain"),
    ]
    IMAGE_POSITION_CHOICES = [
        ("center", "Center"),
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("left", "Left"),
        ("right", "Right"),
    ]
    OVERLAY_CHOICES = [
        ("none", "None"),
        ("light", "Light"),
        ("dark", "Dark"),
        ("brand", "Brand color"),
    ]
    OVERLAY_STRENGTH_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="business_cards")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="business_cards")
    display_name = models.CharField(max_length=160)
    job_title = models.CharField(max_length=120, blank=True)
    headline = models.CharField(max_length=220, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(
        max_length=32,
        blank=True,
        validators=[RegexValidator(r"^[0-9+().\-\s]*$", "Enter a valid phone number.")],
    )
    style = models.CharField(max_length=16, choices=STYLE_CHOICES, default="signature")
    orientation = models.CharField(
        max_length=16,
        choices=ORIENTATION_CHOICES,
        default="landscape",
    )
    font_style = models.CharField(
        max_length=16,
        choices=FONT_STYLE_CHOICES,
        default="modern",
    )
    color_mode = models.CharField(
        max_length=8,
        choices=CUSTOMIZATION_MODE_CHOICES,
        default="style",
    )
    typography_mode = models.CharField(
        max_length=8,
        choices=CUSTOMIZATION_MODE_CHOICES,
        default="style",
    )
    heading_font = models.CharField(
        max_length=16,
        choices=FONT_FAMILY_CHOICES,
        default="cormorant",
    )
    body_font = models.CharField(
        max_length=16,
        choices=FONT_FAMILY_CHOICES,
        default="manrope",
    )
    accent_font = models.CharField(
        max_length=16,
        choices=FONT_FAMILY_CHOICES,
        default="great_vibes",
    )
    custom_font_asset = models.ForeignKey(
        "BusinessAsset",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="business_card_fonts",
    )
    background_color = models.CharField(
        max_length=7,
        default="#0B0B0D",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Enter a six-digit hex color.")],
    )
    text_color = models.CharField(
        max_length=7,
        default="#F8F1E1",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Enter a six-digit hex color.")],
    )
    accent_color = models.CharField(
        max_length=7,
        default="#C8A96B",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Enter a six-digit hex color.")],
    )
    border_color = models.CharField(
        max_length=7,
        default="#BFA36A",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Enter a six-digit hex color.")],
    )
    ornament_color = models.CharField(
        max_length=7,
        default="#C8A96B",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Enter a six-digit hex color.")],
    )
    social_links = models.JSONField(default=list, blank=True)
    show_social_links = models.BooleanField(default=True)
    show_qr = models.BooleanField(default=True)
    background_type = models.CharField(
        max_length=16,
        choices=BACKGROUND_TYPE_CHOICES,
        default="generated",
    )
    background_asset = models.ForeignKey(
        "BusinessAsset",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="business_card_backgrounds",
    )
    background_apply_to = models.CharField(
        max_length=8,
        choices=BACKGROUND_APPLY_CHOICES,
        default="front",
    )
    background_image_fit = models.CharField(
        max_length=8,
        choices=IMAGE_FIT_CHOICES,
        default="cover",
    )
    background_image_position = models.CharField(
        max_length=8,
        choices=IMAGE_POSITION_CHOICES,
        default="center",
    )
    background_overlay = models.CharField(
        max_length=8,
        choices=OVERLAY_CHOICES,
        default="dark",
    )
    background_overlay_strength = models.CharField(
        max_length=8,
        choices=OVERLAY_STRENGTH_CHOICES,
        default="medium",
    )
    show_email = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=True)
    show_business_address = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "user"],
                name="unique_member_business_card",
            )
        ]
        ordering = ["business_id", "user_id"]

    def __str__(self):
        return f"{self.display_name} — {self.business.display_name}"


class AccountProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account_profile")
    phone = models.CharField(max_length=32, blank=True)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["phone"],
                condition=~models.Q(phone=""),
                name="unique_nonblank_account_phone",
            )
        ]


class AccountChallenge(models.Model):
    PURPOSE_CHOICES = [
        ("verify_email", "Verify email"),
        ("reset_password", "Reset password"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account_challenges")
    purpose = models.CharField(max_length=24, choices=PURPOSE_CHOICES)
    code_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField(default=account_challenge_expiry)
    consumed_at = models.DateTimeField(blank=True, null=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "purpose", "expires_at"])]

    @property
    def is_usable(self):
        return self.consumed_at is None and self.expires_at > timezone.now() and self.attempts < 5


class BusinessCapability(models.Model):
    CODE_CHOICES = [
        ("site", "Site"),
        ("sell", "Sell"),
        ("schedule", "Schedule"),
        ("operate", "Operate"),
    ]
    STATUS_CHOICES = [("setup", "Setup"), ("active", "Active"), ("disabled", "Disabled")]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="capabilities")
    code = models.CharField(max_length=16, choices=CODE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="setup")
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "code"], name="unique_business_capability")]
        ordering = ["code"]


class BusinessLocation(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=80)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=24, blank=True)
    country = models.CharField(max_length=2, default="PH")
    timezone = models.CharField(max_length=64, default="Asia/Manila")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "code"], name="unique_business_location_code")]
        ordering = ["-is_primary", "name"]


class BusinessAsset(models.Model):
    TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
        ("document", "Document"),
        ("model", "3D model"),
        ("font", "Font"),
    ]
    PROCESSING_CHOICES = [("processing", "Processing"), ("ready", "Ready"), ("rejected", "Rejected")]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="assets")
    title = models.CharField(max_length=160)
    alt_text = models.CharField(max_length=250, blank=True)
    asset_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    file = models.FileField(upload_to=library_asset_path, max_length=500)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    processing_status = models.CharField(max_length=16, choices=PROCESSING_CHOICES, default="ready")
    validation_error = models.CharField(max_length=300, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="uploaded_business_assets")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]


class BusinessDevice(models.Model):
    TYPE_CHOICES = [
        ("pos", "POS station"),
        ("customer_display", "Customer display"),
        ("kitchen_display", "Fulfillment display"),
        ("dispatch_display", "Delivery display"),
        ("attendance", "Attendance terminal"),
        ("signage", "Digital signage"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="devices")
    location = models.ForeignKey(BusinessLocation, on_delete=models.SET_NULL, blank=True, null=True, related_name="devices")
    name = models.CharField(max_length=120)
    device_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    pairing_code_digest = models.CharField(max_length=64, blank=True, db_index=True)
    pairing_code_encrypted = models.TextField(blank=True)
    pairing_code_issued_at = models.DateTimeField(blank=True, null=True)
    token_version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_business_devices")
    last_seen_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_device_name")]
        ordering = ["device_type", "name"]


class DeviceLink(models.Model):
    LINK_CHOICES = [("customer_display", "Customer display")]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="device_links")
    source_device = models.ForeignKey(BusinessDevice, on_delete=models.CASCADE, related_name="outgoing_links")
    target_device = models.OneToOneField(BusinessDevice, on_delete=models.CASCADE, related_name="incoming_link")
    link_type = models.CharField(max_length=24, choices=LINK_CHOICES, default="customer_display")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_device_links")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source_device", "target_device"], name="unique_device_link_pair"),
        ]
        ordering = ["target_device__name", "id"]


class BusinessInvitation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("revoked", "Revoked"),
        ("expired", "Expired"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=16, choices=BusinessMembership.ROLE_CHOICES, default="staff")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    token_digest = models.CharField(max_length=128, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sent_business_invitations")
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()


class AuditEvent(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="business_audit_events")
    action = models.CharField(max_length=120)
    resource_type = models.CharField(max_length=80)
    resource_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class BusinessEvent(models.Model):
    TYPE_CHOICES = [
        ("task", "Task"),
        ("meeting", "Meeting"),
        ("event", "Event or function"),
        ("appointment", "Appointment"),
        ("deadline", "Deadline"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    SYNC_CHOICES = [
        ("not_connected", "Not connected"),
        ("pending", "Pending"),
        ("synced", "Synced"),
        ("error", "Error"),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=180)
    notes = models.TextField(blank=True, max_length=4000)
    event_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default="task")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="planned")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    resource_layout = models.ForeignKey(
        "scheduling.ResourceLayout",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="business_events",
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_business_events")
    google_calendar_id = models.CharField(max_length=255, blank=True)
    google_event_id = models.CharField(max_length=255, blank=True)
    google_event_url = models.URLField(blank=True)
    google_sync_status = models.CharField(max_length=16, choices=SYNC_CHOICES, default="not_connected")
    google_synced_at = models.DateTimeField(blank=True, null=True)
    google_sync_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "id"]

    def __str__(self):
        return self.title


class GoogleCalendarConnection(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="google_calendar_connection")
    connected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pixelcore_google_calendar_connections",
    )
    google_email = models.EmailField(blank=True)
    calendar_id = models.CharField(max_length=255, default="primary")
    encrypted_access_token = models.TextField(blank=True)
    encrypted_refresh_token = models.TextField(blank=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    scopes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    last_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["business__display_name", "id"]

    def __str__(self):
        return f"Google Calendar for {self.business}"
