from django.contrib import admin

from .models import (
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
    ServiceSession,
    StaffProfile,
    VenueEvent,
)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "business", "employee_code", "employment_status", "is_bookable")
    list_filter = ("employment_status", "is_bookable", "is_active")
    search_fields = ("display_name", "email", "employee_code", "business__display_name")


@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "singular_label", "is_active")


@admin.register(ResourceLayout)
class ResourceLayoutAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "location", "layout_type", "is_active")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "resource_type", "element_type", "location", "capacity", "is_bookable", "is_active")
    list_filter = ("element_type", "resource_type", "is_bookable", "is_active")


@admin.register(SchedulingSettings)
class SchedulingSettingsAdmin(admin.ModelAdmin):
    list_display = ("business", "public_booking_enabled", "advance_booking_days", "updated_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("offering", "business", "customer", "starts_at", "status", "payment_status")
    list_filter = ("status", "payment_status")


@admin.register(ServiceSession)
class ServiceSessionAdmin(admin.ModelAdmin):
    list_display = ("offering", "business", "starts_at", "capacity", "status")


class EventGuestInline(admin.TabularInline):
    model = EventGuest
    extra = 0
    fields = ("full_name", "email", "party_size", "response", "table")


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0


class EventScheduleInline(admin.TabularInline):
    model = EventSchedule
    extra = 0


class EventStoryBlockInline(admin.TabularInline):
    model = EventStoryBlock
    extra = 0


class EventMediaInline(admin.TabularInline):
    model = EventMedia
    extra = 0


@admin.register(VenueEvent)
class VenueEventAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "event_type", "starts_at", "status")
    list_filter = ("event_type", "status", "public_rsvp_enabled")
    search_fields = ("title", "organizer_name", "organizer_email")
    inlines = (
        EventGuestInline,
        EventParticipantInline,
        EventScheduleInline,
        EventStoryBlockInline,
        EventMediaInline,
    )


@admin.register(EventGuest)
class EventGuestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "event", "response", "party_size", "table")
    list_filter = ("response",)
    search_fields = ("full_name", "email", "event__title")


@admin.register(EventQuote)
class EventQuoteAdmin(admin.ModelAdmin):
    list_display = ("event", "is_enabled", "citation")
