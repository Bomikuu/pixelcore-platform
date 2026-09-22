import uuid

from django.conf import settings as django_settings
from django.db import models

from businesses.models import Business, BusinessAsset, BusinessDevice, BusinessLocation


class DisplayPublication(models.Model):
    KIND_CHOICES = [("catalog_board", "Catalog board"), ("promotion", "Promotional poster"), ("information", "Information screen"), ("qr_catalog", "QR catalog")]
    TEMPLATE_CHOICES = [("poster_menu", "Poster Menu"), ("feature_rows", "Feature rows"), ("triple_grid", "Triple grid"), ("hero_list", "Hero and list"), ("freeform", "Freeform canvas"), ("mobile_catalog", "Mobile catalog")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="display_publications")
    location = models.ForeignKey(BusinessLocation, on_delete=models.SET_NULL, blank=True, null=True, related_name="display_publications")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=24, choices=KIND_CHOICES)
    template = models.CharField(max_length=24, choices=TEMPLATE_CHOICES, default="feature_rows")
    schema_version = models.PositiveSmallIntegerField(default=1)
    settings = models.JSONField(default=dict, blank=True)
    offering_ids = models.JSONField(default=list, blank=True)
    background_asset = models.ForeignKey(BusinessAsset, on_delete=models.SET_NULL, blank=True, null=True, related_name="display_backgrounds")
    share_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_display_publications")
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_business_display_name")]
        ordering = ["kind", "name"]


class DisplayDeviceAssignment(models.Model):
    publication = models.ForeignKey(DisplayPublication, on_delete=models.CASCADE, related_name="device_assignments")
    device = models.OneToOneField(BusinessDevice, on_delete=models.CASCADE, related_name="display_assignment")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["publication", "device"], name="unique_publication_device")]
