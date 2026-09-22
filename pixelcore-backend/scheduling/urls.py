from django.urls import path

from .views import (
    AvailabilityExceptionViewSet, AvailabilityRuleViewSet, BookingViewSet, PublicAvailabilityView,
    PublicBookingCreateView, PublicBookingManageView, ServiceAssignmentViewSet, ServiceSessionViewSet,
    StaffProfileViewSet,
    VenueEventGuestCollectionView,
    VenueEventGuestDetailView,
    VenueEventMediaCollectionView,
    VenueEventMediaDetailView,
    VenueEventMusicView,
    VenueEventOrganizerLinkView,
    VenueEventWebsiteView,
    VenueEventViewSet,
    EventGuestInviteLinkView,
    PublicEventOrganizerGuestCollectionView,
    PublicEventOrganizerGuestDetailView,
    PublicEventOrganizerInviteLinkView,
    PublicEventOrganizerView,
    PublicEventRsvpView,
    PublicEventWebsiteView,
    ResourceLayoutViewSet, ResourceTypeViewSet, ResourceViewSet, SchedulingSettingsView,
)


def routes(prefix, viewset, methods_detail=None):
    methods_detail = methods_detail or {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
    return [
        path(f"businesses/<uuid:business_public_id>/{prefix}/", viewset.as_view({"get": "list", "post": "create"})),
        path(f"businesses/<uuid:business_public_id>/{prefix}/<uuid:public_id>/", viewset.as_view(methods_detail)),
    ]


urlpatterns = []
urlpatterns += routes("staff", StaffProfileViewSet)
urlpatterns += routes("resource-types", ResourceTypeViewSet)
urlpatterns += routes("resource-layouts", ResourceLayoutViewSet)
urlpatterns += routes("resources", ResourceViewSet)
urlpatterns += routes("availability", AvailabilityRuleViewSet)
urlpatterns += routes("availability-exceptions", AvailabilityExceptionViewSet)
urlpatterns += routes("service-assignments", ServiceAssignmentViewSet)
urlpatterns += routes("sessions", ServiceSessionViewSet)
urlpatterns += routes("bookings", BookingViewSet, {"get": "retrieve", "patch": "partial_update"})
urlpatterns += routes("venue-events", VenueEventViewSet)
urlpatterns += [
    path("businesses/<uuid:business_public_id>/schedule-settings/", SchedulingSettingsView.as_view()),
    path("public/<slug:slug>/availability/<slug:offering_slug>/", PublicAvailabilityView.as_view()),
    path("public/<slug:slug>/bookings/", PublicBookingCreateView.as_view()),
    path("public/<slug:slug>/bookings/<uuid:booking_id>/", PublicBookingManageView.as_view()),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/guests/",
        VenueEventGuestCollectionView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/guests/<uuid:guest_public_id>/",
        VenueEventGuestDetailView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/organizer-link/",
        VenueEventOrganizerLinkView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/website/",
        VenueEventWebsiteView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/website/media/",
        VenueEventMediaCollectionView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/website/media/<uuid:media_public_id>/",
        VenueEventMediaDetailView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/website/music/",
        VenueEventMusicView.as_view(),
    ),
    path(
        "businesses/<uuid:business_public_id>/venue-events/<uuid:event_public_id>/guests/<uuid:guest_public_id>/invite-link/",
        EventGuestInviteLinkView.as_view(),
    ),
    path(
        "public/events/<uuid:event_public_id>/website/",
        PublicEventWebsiteView.as_view(),
    ),
    path(
        "public/events/<uuid:event_public_id>/rsvp/<str:token>/",
        PublicEventRsvpView.as_view(),
    ),
    path(
        "public/events/<uuid:event_public_id>/manage/<str:token>/",
        PublicEventOrganizerView.as_view(),
    ),
    path(
        "public/events/<uuid:event_public_id>/manage/<str:token>/guests/",
        PublicEventOrganizerGuestCollectionView.as_view(),
    ),
    path(
        "public/events/<uuid:event_public_id>/manage/<str:token>/guests/<uuid:guest_public_id>/",
        PublicEventOrganizerGuestDetailView.as_view(),
    ),
    path(
        "public/events/<uuid:event_public_id>/manage/<str:token>/guests/<uuid:guest_public_id>/invite-link/",
        PublicEventOrganizerInviteLinkView.as_view(),
    ),
]
