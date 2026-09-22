from django.contrib import admin

from .models import (
    AccountChallenge,
    AccountProfile,
    AuditEvent,
    Business,
    BusinessAsset,
    BusinessCard,
    BusinessDevice,
    BusinessEvent,
    BusinessMembership,
    DeviceLink,
    GoogleCalendarConnection,
)


class BusinessMembershipInline(admin.TabularInline):
    model = BusinessMembership
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("display_name", "industry", "status", "country", "updated_at")
    list_filter = ("status", "industry", "country")
    search_fields = ("display_name", "legal_name", "slug", "contact_email")
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [BusinessMembershipInline]


@admin.register(BusinessMembership)
class BusinessMembershipAdmin(admin.ModelAdmin):
    list_display = ("business", "user", "role", "status", "joined_at")
    list_filter = ("role", "status")
    search_fields = ("business__display_name", "user__email")


@admin.register(BusinessCard)
class BusinessCardAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "business",
        "user",
        "style",
        "background_type",
        "is_published",
        "updated_at",
    )
    list_filter = ("style", "orientation", "background_type", "is_published")
    search_fields = ("display_name", "business__display_name", "user__email")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(BusinessEvent)
class BusinessEventAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "event_type", "status", "starts_at", "google_sync_status")
    list_filter = ("event_type", "status", "google_sync_status")
    search_fields = ("title", "business__display_name")


@admin.register(GoogleCalendarConnection)
class GoogleCalendarConnectionAdmin(admin.ModelAdmin):
    list_display = ("business", "google_email", "is_active", "last_synced_at", "updated_at")
    exclude = ("encrypted_access_token", "encrypted_refresh_token")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "email_verified_at", "updated_at")
    search_fields = ("user__email", "user__username", "phone")


@admin.register(AccountChallenge)
class AccountChallengeAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "expires_at", "consumed_at", "attempts")
    list_filter = ("purpose",)
    readonly_fields = ("public_id", "code_digest", "created_at")


@admin.register(BusinessDevice)
class BusinessDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "device_type", "is_active", "last_seen_at")
    list_filter = ("device_type", "is_active")
    search_fields = ("name", "business__display_name")
    readonly_fields = ("public_id", "pairing_code_digest", "token_version", "created_at", "updated_at")


@admin.register(DeviceLink)
class DeviceLinkAdmin(admin.ModelAdmin):
    list_display = ("source_device", "target_device", "link_type", "is_active", "updated_at")
    list_filter = ("link_type", "is_active")
    search_fields = ("business__display_name", "source_device__name", "target_device__name")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "business", "resource_type", "actor", "created_at")
    list_filter = ("action", "resource_type")
    search_fields = ("business__display_name", "resource_id")
    readonly_fields = ("business", "actor", "action", "resource_type", "resource_id", "metadata", "created_at")


@admin.register(BusinessAsset)
class BusinessAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "asset_type", "processing_status", "size_bytes", "created_at")
    list_filter = ("asset_type", "processing_status")
    search_fields = ("title", "business__display_name")
    readonly_fields = ("public_id", "mime_type", "size_bytes", "processing_status", "validation_error", "metadata", "created_at")
