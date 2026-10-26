import uuid

from django.conf import settings
from django.db import models

from businesses.models import Business
from .blocks import validate_page_content


class Site(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="site")
    name = models.CharField(max_length=160)
    status = models.CharField(max_length=16, choices=[("draft", "Draft"), ("published", "Published")], default="draft")
    navigation = models.JSONField(default=list, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    cache_version = models.PositiveBigIntegerField(default=1)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SitePage(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180)
    page_type = models.CharField(max_length=20, choices=[("standard", "Standard"), ("home", "Home"), ("policy", "Policy")], default="standard")
    status = models.CharField(max_length=16, choices=[("draft", "Draft"), ("published", "Published")], default="draft")
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=180, blank=True)
    no_index = models.BooleanField(default=False)
    draft_revision = models.ForeignKey("PageRevision", on_delete=models.SET_NULL, blank=True, null=True, related_name="draft_for_pages")
    published_revision = models.ForeignKey("PageRevision", on_delete=models.SET_NULL, blank=True, null=True, related_name="published_for_pages")
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["site", "slug"], name="unique_site_page_slug")]
        ordering = ["title", "id"]

    @property
    def business(self):
        return self.site.business


class PageRevision(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    page = models.ForeignKey(SitePage, on_delete=models.CASCADE, related_name="revisions")
    number = models.PositiveIntegerField()
    schema_version = models.PositiveIntegerField(default=1)
    content = models.JSONField(validators=[validate_page_content])
    checksum = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_page_revisions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["page", "number"], name="unique_page_revision_number")]
        ordering = ["-number"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Page revisions are immutable.")
        super().save(*args, **kwargs)


class SiteDomain(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="domains")
    hostname = models.CharField(max_length=253, unique=True)
    is_platform_subdomain = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=80, blank=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def business(self):
        return self.site.business


class StudioHandoff(models.Model):
    digest = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE)
    state = models.CharField(max_length=128)
    audience = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)


class StudioGrant(models.Model):
    digest = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
