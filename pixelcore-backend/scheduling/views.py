import secrets
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.api import BusinessScopedModelViewSet
from businesses.models import Business
from businesses.services import record_audit
from businesses.views import member_business
from catalog.models import Offering
from commerce.services import PaymentProviderError, create_paymongo_checkout
from .models import (
    AvailabilityException,
    AvailabilityRule,
    Booking,
    EventGuest,
    EventMedia,
    Resource,
    ResourceLayout,
    ResourceType,
    SchedulingSettings,
    ServiceAssignment,
    ServiceSession,
    StaffProfile,
    VenueEvent,
)
from .serializers import (
    AvailabilityExceptionSerializer,
    AvailabilityRuleSerializer,
    BookingSerializer,
    EventGuestSerializer,
    EventMediaSerializer,
    EventMusicUploadSerializer,
    EventInviteActionSerializer,
    PublicBookingInputSerializer,
    PublicRsvpSerializer,
    ResourceLayoutSerializer,
    ResourceSerializer,
    ResourceTypeSerializer,
    SchedulingSettingsSerializer,
    ServiceAssignmentSerializer,
    ServiceSessionSerializer,
    StaffProfileSerializer,
    VenueEventSerializer,
    VenueEventWebsiteSerializer,
)
from .services import (
    BookingConflict,
    booking_token_digest,
    create_booking,
    event_access_token_digest,
    issue_event_access_token,
    project_booking_event,
    project_venue_event,
    read_event_access_token,
    reschedule_booking,
)
from .tasks import send_event_guest_invitation


class StaffProfileViewSet(BusinessScopedModelViewSet):
    queryset = StaffProfile.objects.select_related("membership")
    serializer_class = StaffProfileSerializer
    audit_resource = "staff_profile"


class ResourceTypeViewSet(BusinessScopedModelViewSet):
    queryset = ResourceType.objects.all()
    serializer_class = ResourceTypeSerializer
    audit_resource = "resource_type"


class ResourceLayoutViewSet(BusinessScopedModelViewSet):
    queryset = ResourceLayout.objects.select_related("location")
    serializer_class = ResourceLayoutSerializer
    audit_resource = "resource_layout"


class ResourceViewSet(BusinessScopedModelViewSet):
    queryset = Resource.objects.select_related("resource_type", "location", "layout")
    serializer_class = ResourceSerializer
    audit_resource = "resource"


class AvailabilityRuleViewSet(BusinessScopedModelViewSet):
    queryset = AvailabilityRule.objects.select_related("staff", "location")
    serializer_class = AvailabilityRuleSerializer
    audit_resource = "availability_rule"


class AvailabilityExceptionViewSet(BusinessScopedModelViewSet):
    queryset = AvailabilityException.objects.select_related("staff")
    serializer_class = AvailabilityExceptionSerializer
    audit_resource = "availability_exception"


class ServiceAssignmentViewSet(BusinessScopedModelViewSet):
    queryset = ServiceAssignment.objects.select_related("staff", "offering", "location")
    serializer_class = ServiceAssignmentSerializer
    audit_resource = "service_assignment"


class ServiceSessionViewSet(BusinessScopedModelViewSet):
    queryset = ServiceSession.objects.select_related("staff", "offering", "location")
    serializer_class = ServiceSessionSerializer
    audit_resource = "service_session"


class BookingViewSet(BusinessScopedModelViewSet):
    queryset = Booking.objects.select_related("customer", "offering", "staff", "location", "session", "event").prefetch_related("resources")
    serializer_class = BookingSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    audit_resource = "booking"

    def create(self, request, *args, **kwargs):
        business = self.get_business()
        serializer = PublicBookingInputSerializer(
            data=request.data,
            context={"business": business},
        )
        serializer.is_valid(raise_exception=True)
        try:
            booking, _ = create_booking(
                business,
                serializer.validated_data,
                actor=request.user,
            )
        except BookingConflict as exc:
            return Response(
                {
                    "error": {
                        "code": "BOOKING_CONFLICT",
                        "message": str(exc),
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            BookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        booking = serializer.save()
        if previous_status != "cancelled" and booking.status == "cancelled" and booking.cancelled_at is None:
            booking.cancelled_at = timezone.now()
            booking.save(update_fields=["cancelled_at", "updated_at"])
        project_booking_event(booking, self.request.user)
        record_audit(self.get_business(), self.request.user, "booking.updated", "booking", booking.public_id)


class VenueEventViewSet(BusinessScopedModelViewSet):
    queryset = VenueEvent.objects.select_related(
        "business",
        "location",
        "layout",
        "handler",
        "calendar_event",
    ).prefetch_related(
        "guests",
        "assigned_staff",
        "products__assets",
        "products__ordered_media__asset",
    )
    serializer_class = VenueEventSerializer
    audit_resource = "venue_event"

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        event_type = self.request.query_params.get("event_type", "").strip()
        event_status = self.request.query_params.get("status", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(organizer_name__icontains=search)
                | Q(location__name__icontains=search)
            )
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if event_status:
            queryset = queryset.filter(status=event_status)
        return queryset.order_by("starts_at", "id")

    def perform_create(self, serializer):
        event = serializer.save(
            business=self.get_business(),
            created_by=self.request.user,
        )
        project_venue_event(event, self.request.user)
        record_audit(
            self.get_business(),
            self.request.user,
            "venue_event.created",
            "venue_event",
            event.public_id,
        )

    def perform_update(self, serializer):
        event = serializer.save()
        project_venue_event(event, self.request.user)
        record_audit(
            self.get_business(),
            self.request.user,
            "venue_event.updated",
            "venue_event",
            event.public_id,
        )


class SchedulingSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_business(self, request, business_public_id, management=False):
        roles = ("owner", "admin", "manager") if management else ("owner", "admin", "manager", "staff")
        return get_object_or_404(
            Business.objects.filter(
                public_id=business_public_id,
                memberships__user=request.user,
                memberships__status="active",
                memberships__role__in=roles,
            ).distinct()
        )

    def get(self, request, business_public_id):
        business = self.get_business(request, business_public_id)
        settings_record, _ = SchedulingSettings.objects.get_or_create(business=business)
        return Response(SchedulingSettingsSerializer(settings_record).data)

    def patch(self, request, business_public_id):
        business = self.get_business(request, business_public_id, management=True)
        settings_record, _ = SchedulingSettings.objects.get_or_create(business=business)
        serializer = SchedulingSettingsSerializer(settings_record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit(
            business,
            request.user,
            "scheduling.settings_updated",
            "scheduling_settings",
            business.public_id,
        )
        return Response(serializer.data)


class PublicAvailabilityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, offering_slug):
        offering = get_object_or_404(
            Offering,
            business__slug=slug,
            business__status="active",
            slug=offering_slug,
            offering_type="service",
            status="published",
        )
        settings_record = SchedulingSettings.objects.filter(business=offering.business).first()
        if settings_record and not settings_record.public_booking_enabled:
            return Response(
                {
                    "error": {
                        "code": "PUBLIC_BOOKING_DISABLED",
                        "message": "Online booking is not currently available.",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            start_date = date.fromisoformat(request.query_params.get("start", str(timezone.localdate())))
            end_date = date.fromisoformat(request.query_params.get("end", str(start_date + timedelta(days=14))))
        except ValueError:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Use ISO dates for start and end.", "details": {}}}, status=400)
        advance_booking_days = settings_record.advance_booking_days if settings_record else 31
        if end_date < start_date or (end_date - start_date).days > min(advance_booking_days, 31):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Availability ranges exceed the configured booking window.", "details": {}}}, status=400)
        duration = timedelta(minutes=offering.duration_minutes or 60)
        requested_ids = []
        for value in request.query_params.getlist("resource_public_ids"):
            requested_ids.extend(part for part in value.split(",") if part)
        resources = list(
            Resource.objects.filter(
                business=offering.business,
                is_active=True,
                is_bookable=True,
            ).select_related("resource_type", "location", "layout")
        )
        selected_resources = [resource for resource in resources if str(resource.public_id) in requested_ids]
        if requested_ids and len(selected_resources) != len(set(requested_ids)):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "One or more selected resources are unavailable.", "details": {}}}, status=400)
        try:
            seats = max(1, min(int(request.query_params.get("seats", 1)), 50))
        except (TypeError, ValueError):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Seats must be a number from 1 to 50.", "details": {}}}, status=400)
        slots = []
        assignments = offering.staff_assignments.filter(is_active=True, staff__is_active=True, staff__is_bookable=True).select_related("staff")
        for assignment in assignments:
            staff = assignment.staff
            try:
                zone = ZoneInfo(staff.timezone)
            except ZoneInfoNotFoundError:
                zone = ZoneInfo("Asia/Manila")
            current_date = start_date
            while current_date <= end_date and len(slots) < 200:
                rules = staff.availability_rules.filter(is_active=True, weekday=current_date.weekday()).filter(business=offering.business)
                for rule in rules:
                    cursor = datetime.combine(current_date, rule.starts_at, tzinfo=zone)
                    boundary = datetime.combine(current_date, rule.ends_at, tzinfo=zone)
                    while cursor + duration <= boundary and len(slots) < 200:
                        slot_end = cursor + duration
                        blocked = staff.availability_exceptions.filter(starts_at__lt=slot_end, ends_at__gt=cursor).exclude(exception_type="available").exists()
                        occupied = staff.bookings.filter(status__in=("pending", "confirmed"), starts_at__lt=slot_end, ends_at__gt=cursor).exists()
                        available_resources = [
                            resource
                            for resource in resources
                            if resource.capacity >= seats
                            and (not rule.location_id or resource.location_id == rule.location_id)
                            and not resource.bookings.filter(
                                status__in=("pending", "confirmed"),
                                starts_at__lt=slot_end,
                                ends_at__gt=cursor,
                            ).exists()
                        ]
                        available_resource_ids = {
                            str(resource.public_id) for resource in available_resources
                        }
                        resource_blocked = any(
                            resource.capacity < seats
                            or (rule.location_id and resource.location_id != rule.location_id)
                            or str(resource.public_id) not in available_resource_ids
                            for resource in selected_resources
                        )
                        if not blocked and not occupied and not resource_blocked and cursor >= timezone.now():
                            slots.append({
                                "starts_at": cursor.isoformat(),
                                "ends_at": slot_end.isoformat(),
                                "staff_public_id": str(staff.public_id),
                                "staff_name": staff.display_name,
                                "location_public_id": str(rule.location.public_id) if rule.location else None,
                                "resource_public_ids": [str(resource.public_id) for resource in selected_resources],
                                "available_resource_public_ids": sorted(available_resource_ids),
                            })
                        cursor = slot_end
                current_date += timedelta(days=1)
        sessions = offering.sessions.filter(status="scheduled", starts_at__date__range=(start_date, end_date)).order_by("starts_at")
        sessions = [session for session in sessions if (session.capacity - sum(item.seats for item in session.bookings.filter(status__in=("pending", "confirmed")))) >= seats]
        return Response({"slots": slots, "sessions": ServiceSessionSerializer(sessions, many=True).data, "resources": ResourceSerializer(resources, many=True, context={"business": offering.business}).data})


class PublicBookingCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        settings_record = SchedulingSettings.objects.filter(business=business).first()
        if settings_record and not settings_record.public_booking_enabled:
            return Response(
                {
                    "error": {
                        "code": "PUBLIC_BOOKING_DISABLED",
                        "message": "Online booking is not currently available.",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = PublicBookingInputSerializer(data=request.data, context={"business": business})
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["requires_approval"] = (
            business.industry_preset == "restaurant"
            or bool(serializer.validated_data["offering"].metadata.get("booking_requires_approval"))
        )
        payment_method = serializer.validated_data.get("payment_method")
        success_url = serializer.validated_data.get("success_url", "")
        cancel_url = serializer.validated_data.get("cancel_url", "")
        try:
            booking, token = create_booking(business, serializer.validated_data)
        except BookingConflict as exc:
            return Response({"error": {"code": "BOOKING_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        payload = {**BookingSerializer(booking).data, "management_token": token}
        if booking.order_id and payment_method == "paymongo":
            try:
                attempt = create_paymongo_checkout(booking.order, success_url, cancel_url, f"booking-{booking.public_id}")
                payload["checkout_url"] = attempt.checkout_url
            except PaymentProviderError as exc:
                payload["payment_error"] = str(exc)
        return Response(payload, status=status.HTTP_201_CREATED)


def authorized_booking(request, slug, booking_id):
    booking = get_object_or_404(Booking.objects.select_related("business", "customer", "offering", "staff"), business__slug=slug, public_id=booking_id)
    supplied = request.headers.get("X-Booking-Token", "")
    if not secrets.compare_digest(booking.cancellation_token_digest, booking_token_digest(supplied)):
        return None, Response({"error": {"code": "BOOKING_ACCESS_DENIED", "message": "This booking cannot be managed.", "details": {}}}, status=403)
    return booking, None


class PublicBookingManageView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug, booking_id):
        booking, error = authorized_booking(request, slug, booking_id)
        return error or Response(BookingSerializer(booking).data)

    def patch(self, request, slug, booking_id):
        booking, error = authorized_booking(request, slug, booking_id)
        if error:
            return error
        if request.data.get("action") == "cancel":
            if booking.status == "cancelled":
                return Response(BookingSerializer(booking).data)
            if booking.status not in {"pending", "confirmed"}:
                return Response({"error": {"code": "BOOKING_CONFLICT", "message": "This booking can no longer be cancelled.", "details": {}}}, status=409)
            booking.status = "cancelled"
            booking.cancelled_at = timezone.now()
            booking.save(update_fields=["status", "cancelled_at", "updated_at"])
            project_booking_event(booking)
            record_audit(booking.business, None, "booking.cancelled", "booking", booking.public_id)
        elif request.data.get("action") == "reschedule":
            try:
                starts_at = datetime.fromisoformat(request.data["starts_at"])
                ends_at = datetime.fromisoformat(request.data["ends_at"])
                booking = reschedule_booking(booking, starts_at, ends_at)
            except (KeyError, ValueError):
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "Valid start and end date-times are required.", "details": {}}}, status=400)
            except BookingConflict as exc:
                return Response({"error": {"code": "BOOKING_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        else:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose cancel or reschedule.", "details": {}}}, status=400)
        return Response(BookingSerializer(booking).data)


def workspace_venue_event(request, business_public_id, event_public_id, management=False):
    roles = ("owner", "admin", "manager") if management else (
        "owner",
        "admin",
        "manager",
        "staff",
    )
    business = member_business(request.user, business_public_id, roles=roles)
    event = get_object_or_404(
        VenueEvent.objects.select_related("business", "location", "layout")
        .prefetch_related("guests"),
        business=business,
        public_id=event_public_id,
    )
    return business, event


def serialize_event_guest(guest, request, event):
    return EventGuestSerializer(
        guest,
        context={"request": request, "event": event},
    ).data


class EventGuestPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def event_guest_summary(event, guests):
    tables = []
    summaries_by_id = {}
    if event.layout_id:
        for table in Resource.objects.filter(
            layout=event.layout,
            is_active=True,
            element_type__in=("table", "booth"),
        ).order_by("name", "id"):
            summary = {
                "public_id": str(table.public_id),
                "name": table.name,
                "capacity": table.capacity,
                "guest_count": 0,
                "assigned_seats": 0,
                "guest_names": [],
            }
            tables.append(summary)
            summaries_by_id[table.id] = summary

    unassigned = 0
    for guest in guests:
        if not guest.table_id:
            unassigned += 1
            continue
        summary = summaries_by_id.get(guest.table_id)
        if not summary:
            continue
        summary["guest_count"] += 1
        if guest.response != "declined":
            summary["assigned_seats"] += guest.party_size
        if len(summary["guest_names"]) < 3:
            summary["guest_names"].append(guest.full_name)

    return {
        "total": len(guests),
        "unassigned": unassigned,
        "tables": tables,
    }


class VenueEventGuestCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_public_id, event_public_id):
        _, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
        )
        guests = list(event.guests.select_related("table"))
        uses_list_controls = any(
            parameter in request.query_params
            for parameter in ("page", "page_size", "table")
        )
        if not uses_list_controls:
            return Response(
                EventGuestSerializer(
                    guests,
                    many=True,
                    context={"request": request, "event": event},
                ).data
            )

        summary = event_guest_summary(event, guests)
        table_filter = request.query_params.get("table", "all")
        if table_filter == "unassigned":
            filtered_guests = [guest for guest in guests if not guest.table_id]
        elif table_filter == "all":
            filtered_guests = guests
        else:
            valid_table_ids = {table["public_id"] for table in summary["tables"]}
            if table_filter not in valid_table_ids:
                return Response(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Choose a table from this event's venue layout.",
                            "details": {"table": ["Choose a valid event table."]},
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            filtered_guests = [
                guest
                for guest in guests
                if str(guest.table.public_id) == table_filter
            ]

        paginator = EventGuestPagination()
        page = paginator.paginate_queryset(filtered_guests, request, view=self)
        serialized = EventGuestSerializer(
            page,
            many=True,
            context={"request": request, "event": event},
        ).data
        response = paginator.get_paginated_response(serialized)
        response.data["page"] = paginator.page.number
        response.data["page_size"] = paginator.get_page_size(request)
        response.data["summary"] = summary
        return response

    def post(self, request, business_public_id, event_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        serializer = EventGuestSerializer(
            data=request.data,
            context={"request": request, "event": event},
        )
        serializer.is_valid(raise_exception=True)
        guest = serializer.save(event=event)
        record_audit(
            business,
            request.user,
            "event_guest.created",
            "event_guest",
            guest.public_id,
        )
        return Response(
            serialize_event_guest(guest, request, event),
            status=status.HTTP_201_CREATED,
        )


class VenueEventGuestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_guest(self, request, business_public_id, event_public_id, guest_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        guest = get_object_or_404(
            EventGuest.objects.select_related("table"),
            event=event,
            public_id=guest_public_id,
        )
        return business, event, guest

    def patch(self, request, business_public_id, event_public_id, guest_public_id):
        business, event, guest = self.get_guest(
            request,
            business_public_id,
            event_public_id,
            guest_public_id,
        )
        serializer = EventGuestSerializer(
            guest,
            data=request.data,
            partial=True,
            context={"request": request, "event": event},
        )
        serializer.is_valid(raise_exception=True)
        guest = serializer.save()
        if "response" in serializer.validated_data:
            guest.responded_at = (
                None if guest.response == "pending" else timezone.now()
            )
            guest.save(update_fields=["responded_at", "updated_at"])
        record_audit(
            business,
            request.user,
            "event_guest.updated",
            "event_guest",
            guest.public_id,
        )
        return Response(serialize_event_guest(guest, request, event))

    def delete(self, request, business_public_id, event_public_id, guest_public_id):
        business, _, guest = self.get_guest(
            request,
            business_public_id,
            event_public_id,
            guest_public_id,
        )
        guest_id = guest.public_id
        guest.delete()
        record_audit(
            business,
            request.user,
            "event_guest.deleted",
            "event_guest",
            guest_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class VenueEventWebsiteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_event(self, request, business_public_id, event_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        event = VenueEvent.objects.select_related(
            "business",
            "location",
        ).prefetch_related(
            "participants__image",
            "schedule_entries",
            "story_blocks__image",
            "media",
            "guests",
        ).get(pk=event.pk)
        return business, event

    def get(self, request, business_public_id, event_public_id):
        _, event = self.get_event(
            request,
            business_public_id,
            event_public_id,
        )
        return Response(
            VenueEventWebsiteSerializer(
                event,
                context={"request": request},
            ).data
        )

    def patch(self, request, business_public_id, event_public_id):
        business, event = self.get_event(
            request,
            business_public_id,
            event_public_id,
        )
        was_enabled = event.website_enabled
        serializer = VenueEventWebsiteSerializer(
            event,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        project_venue_event(event, request.user)
        if event.website_enabled and not event.website_published_at:
            event.website_published_at = timezone.now()
            event.save(update_fields=["website_published_at", "updated_at"])
        elif not event.website_enabled and event.website_published_at:
            event.website_published_at = None
            event.save(update_fields=["website_published_at", "updated_at"])
        record_audit(
            business,
            request.user,
            (
                "venue_event.website_published"
                if event.website_enabled and not was_enabled
                else "venue_event.website_updated"
            ),
            "venue_event",
            event.public_id,
        )
        event.refresh_from_db()
        return Response(
            VenueEventWebsiteSerializer(
                event,
                context={"request": request},
            ).data
        )


class VenueEventMediaCollectionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    SINGLE_IMAGE_PLACEMENTS = {"hero", "popup", "closing"}

    def post(self, request, business_public_id, event_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        serializer = EventMediaSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        placement = serializer.validated_data.get("placement", "gallery")
        existing_singletons = []
        if placement in self.SINGLE_IMAGE_PLACEMENTS:
            existing_singletons = list(
                EventMedia.objects.filter(event=event, placement=placement)
            )
        elif serializer.validated_data.get("is_featured"):
            EventMedia.objects.filter(
                event=event,
                placement=placement,
            ).update(is_featured=False)
        media = serializer.save(
            event=event,
            is_featured=(
                True
                if placement in self.SINGLE_IMAGE_PLACEMENTS
                else serializer.validated_data.get("is_featured", False)
            ),
        )
        for existing in existing_singletons:
            existing.image.delete(save=False)
            existing.delete()
        record_audit(
            business,
            request.user,
            "venue_event.media_added",
            "event_media",
            media.public_id,
        )
        return Response(
            EventMediaSerializer(
                media,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class VenueEventMediaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_media(
        self,
        request,
        business_public_id,
        event_public_id,
        media_public_id,
    ):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        media = get_object_or_404(
            EventMedia,
            event=event,
            public_id=media_public_id,
        )
        return business, event, media

    def patch(
        self,
        request,
        business_public_id,
        event_public_id,
        media_public_id,
    ):
        business, event, media = self.get_media(
            request,
            business_public_id,
            event_public_id,
            media_public_id,
        )
        serializer = EventMediaSerializer(
            media,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("is_featured"):
            placement = serializer.validated_data.get("placement", media.placement)
            EventMedia.objects.filter(
                event=event,
                placement=placement,
            ).exclude(pk=media.pk).update(is_featured=False)
        media = serializer.save()
        record_audit(
            business,
            request.user,
            "venue_event.media_updated",
            "event_media",
            media.public_id,
        )
        return Response(
            EventMediaSerializer(
                media,
                context={"request": request},
            ).data
        )

    def delete(
        self,
        request,
        business_public_id,
        event_public_id,
        media_public_id,
    ):
        business, _, media = self.get_media(
            request,
            business_public_id,
            event_public_id,
            media_public_id,
        )
        media_id = media.public_id
        media.delete()
        record_audit(
            business,
            request.user,
            "venue_event.media_removed",
            "event_media",
            media_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class VenueEventMusicView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, business_public_id, event_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        serializer = EventMusicUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if event.background_music:
            event.background_music.delete(save=False)
        event.background_music = serializer.validated_data["file"]
        event.background_music_title = serializer.validated_data.get("title", "")
        event.music_enabled = True
        event.save(
            update_fields=[
                "background_music",
                "background_music_title",
                "music_enabled",
                "updated_at",
            ]
        )
        record_audit(
            business,
            request.user,
            "venue_event.music_uploaded",
            "venue_event",
            event.public_id,
        )
        return Response(
            VenueEventWebsiteSerializer(
                event,
                context={"request": request},
            ).data
        )

    def delete(self, request, business_public_id, event_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        if event.background_music:
            event.background_music.delete(save=False)
        event.background_music = None
        event.background_music_title = ""
        event.music_enabled = False
        event.save(
            update_fields=[
                "background_music",
                "background_music_title",
                "music_enabled",
                "updated_at",
            ]
        )
        record_audit(
            business,
            request.user,
            "venue_event.music_removed",
            "venue_event",
            event.public_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class VenueEventOrganizerLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_public_id, event_public_id):
        _, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        token = read_event_access_token(event, "organizer_token_digest")
        return Response(
            {
                "has_link": bool(event.organizer_token_digest),
                "recoverable": bool(token),
                "token": token or None,
            }
        )

    def post(self, request, business_public_id, event_public_id):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        serializer = EventInviteActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = read_event_access_token(event, "organizer_token_digest")
        generated = serializer.validated_data["regenerate"] or not token
        if generated:
            had_link = bool(event.organizer_token_digest)
            token = issue_event_access_token(event, "organizer_token_digest")
            record_audit(
                business,
                request.user,
                (
                    "venue_event.organizer_link_rotated"
                    if had_link
                    else "venue_event.organizer_link_created"
                ),
                "venue_event",
                event.public_id,
            )
        return Response(
            {
                "has_link": True,
                "recoverable": True,
                "generated": generated,
                "token": token,
            }
        )


class EventGuestInviteLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        business_public_id,
        event_public_id,
        guest_public_id,
    ):
        business, event = workspace_venue_event(
            request,
            business_public_id,
            event_public_id,
            management=True,
        )
        guest = get_object_or_404(
            EventGuest,
            event=event,
            public_id=guest_public_id,
        )
        serializer = EventInviteActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        should_send = serializer.validated_data["send_email"]
        if should_send and not guest.email:
            return Response(
                {
                    "error": {
                        "code": "INVITATION_EMAIL_REQUIRED",
                        "message": "Add an email address before sending this invitation.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = read_event_access_token(guest, "invite_token_digest")
        generated = serializer.validated_data["regenerate"] or not token
        if generated:
            token = issue_event_access_token(guest, "invite_token_digest")
            record_audit(
                business,
                request.user,
                "event_guest.invite_link_generated",
                "event_guest",
                guest.public_id,
            )

        if should_send:
            send_event_guest_invitation.delay(guest.pk, token)
            guest.invite_sent_at = timezone.now()
            guest.save(update_fields=["invite_sent_at", "updated_at"])
            record_audit(
                business,
                request.user,
                "event_guest.invitation_emailed",
                "event_guest",
                guest.public_id,
            )
        return Response(
            {
                "generated": generated,
                "sent": should_send,
                "invite_sent_at": guest.invite_sent_at,
                "token": token,
            }
        )


def public_event_payload(event, request):
    business = event.business
    logo_url = (
        request.build_absolute_uri(business.logo.url)
        if business.logo
        else None
    )
    payload = {
        "public_id": str(event.public_id),
        "title": event.title,
        "event_type": event.event_type,
        "status": event.status,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "timezone": event.timezone,
        "description": event.description,
        "max_guests": event.max_guests,
        "public_rsvp_enabled": event.public_rsvp_enabled,
        "location": {
            "name": event.location.name,
            "address": event.location.address,
            "city": event.location.city,
            "region": event.location.region,
            "postal_code": event.location.postal_code,
            "country": event.location.country,
            "latitude": event.location.latitude,
            "longitude": event.location.longitude,
        }
        if event.location
        else None,
        "layout": {
            "public_id": str(event.layout.public_id),
            "name": event.layout.name,
            "layout_type": event.layout.layout_type,
        }
        if event.layout
        else None,
        "business": {
            "display_name": business.display_name,
            "slug": business.slug,
            "logo": logo_url,
        },
    }
    payload["website"] = VenueEventWebsiteSerializer(
        event,
        context={"request": request, "public": True},
    ).data
    return payload


def public_event_tables(event):
    if not event.layout_id:
        return []
    return ResourceSerializer(
        event.layout.resources.filter(
            business=event.business,
            is_active=True,
            element_type__in=("table", "booth"),
        ).select_related("resource_type", "location", "layout"),
        many=True,
        context={"business": event.business},
    ).data


def authorized_public_event(event_public_id, token, organizer=False):
    event = get_object_or_404(
        VenueEvent.objects.select_related(
            "business",
            "location",
            "layout",
        ).prefetch_related(
            "participants__image",
            "schedule_entries",
            "story_blocks__image",
            "media",
            "guests",
        ),
        public_id=event_public_id,
        business__status="active",
    )
    field = "organizer_token_digest" if organizer else "invite_token_digest"
    expected = getattr(event, field, "") if organizer else ""
    if organizer and expected and secrets.compare_digest(
        expected,
        event_access_token_digest(token),
    ):
        return event
    return None


def authorized_public_guest(event_public_id, token):
    event = get_object_or_404(
        VenueEvent.objects.select_related(
            "business",
            "location",
            "layout",
        ).prefetch_related(
            "participants__image",
            "schedule_entries",
            "story_blocks__image",
            "media",
            "guests",
        ),
        public_id=event_public_id,
        business__status="active",
    )
    supplied_digest = event_access_token_digest(token)
    guest = event.guests.select_related("table").filter(
        invite_token_digest=supplied_digest,
    ).first()
    return event, guest


def event_access_denied():
    return Response(
        {
            "error": {
                "code": "EVENT_ACCESS_DENIED",
                "message": "This event link is invalid or has been replaced.",
                "details": {},
            }
        },
        status=status.HTTP_403_FORBIDDEN,
    )


class PublicEventWebsiteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, event_public_id):
        event = get_object_or_404(
            VenueEvent.objects.select_related(
                "business",
                "location",
                "layout",
            ).prefetch_related(
                "participants__image",
                "schedule_entries",
                "story_blocks__image",
                "media",
                "guests",
            ),
            public_id=event_public_id,
            business__status="active",
            website_enabled=True,
        )
        return Response({"event": public_event_payload(event, request)})


def event_rsvp_deadline(event):
    sections = event.sections_config if isinstance(event.sections_config, dict) else {}
    rsvp = sections.get("rsvp") if isinstance(sections.get("rsvp"), dict) else {}
    value = rsvp.get("deadline")
    if not value or not isinstance(value, str):
        return None
    try:
        deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if timezone.is_naive(deadline):
        try:
            event_timezone = ZoneInfo(event.timezone)
        except (ZoneInfoNotFoundError, TypeError, ValueError):
            event_timezone = timezone.get_current_timezone()
        deadline = timezone.make_aware(deadline, event_timezone)
    return deadline


class PublicEventRsvpView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, event_public_id, token):
        event, guest = authorized_public_guest(event_public_id, token)
        if not guest:
            return event_access_denied()
        return Response(
            {
                "event": public_event_payload(event, request),
                "guest": serialize_event_guest(guest, request, event),
            }
        )

    def patch(self, request, event_public_id, token):
        event, guest = authorized_public_guest(event_public_id, token)
        if not guest:
            return event_access_denied()
        deadline = event_rsvp_deadline(event)
        if (
            not event.public_rsvp_enabled
            or event.status != "open"
            or (deadline and timezone.now() >= deadline)
        ):
            return Response(
                {
                    "error": {
                        "code": "RSVP_CLOSED",
                        "message": "RSVP responses are closed for this event.",
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        serializer = PublicRsvpSerializer(
            data=request.data,
            context={"event": event, "guest": guest},
        )
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(guest, field, value)
        guest.responded_at = timezone.now()
        guest.save(
            update_fields=[
                *serializer.validated_data.keys(),
                "responded_at",
                "updated_at",
            ]
        )
        record_audit(
            event.business,
            None,
            "event_guest.rsvp_updated",
            "event_guest",
            guest.public_id,
        )
        return Response(
            {
                "event": public_event_payload(event, request),
                "guest": serialize_event_guest(guest, request, event),
            }
        )


def organizer_event(event_public_id, token):
    return authorized_public_event(event_public_id, token, organizer=True)


class PublicEventOrganizerView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, event_public_id, token):
        event = organizer_event(event_public_id, token)
        if not event:
            return event_access_denied()
        return Response(
            {
                "event": public_event_payload(event, request),
                "guest_counts": VenueEventSerializer(
                    event,
                    context={"business": event.business},
                ).data["guest_counts"],
                "tables": public_event_tables(event),
                "guests": EventGuestSerializer(
                    event.guests.select_related("table"),
                    many=True,
                    context={"request": request, "event": event},
                ).data,
            }
        )


class PublicEventOrganizerGuestCollectionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, event_public_id, token):
        event = organizer_event(event_public_id, token)
        if not event:
            return event_access_denied()
        serializer = EventGuestSerializer(
            data=request.data,
            context={"request": request, "event": event},
        )
        serializer.is_valid(raise_exception=True)
        guest = serializer.save(event=event)
        record_audit(
            event.business,
            None,
            "event_guest.organizer_created",
            "event_guest",
            guest.public_id,
        )
        return Response(
            serialize_event_guest(guest, request, event),
            status=status.HTTP_201_CREATED,
        )


class PublicEventOrganizerGuestDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_guest(self, event_public_id, token, guest_public_id):
        event = organizer_event(event_public_id, token)
        if not event:
            return None, None
        guest = event.guests.select_related("table").filter(
            public_id=guest_public_id,
        ).first()
        return event, guest

    def patch(self, request, event_public_id, token, guest_public_id):
        event, guest = self.get_guest(event_public_id, token, guest_public_id)
        if not event or not guest:
            return event_access_denied()
        serializer = EventGuestSerializer(
            guest,
            data=request.data,
            partial=True,
            context={"request": request, "event": event},
        )
        serializer.is_valid(raise_exception=True)
        guest = serializer.save()
        if "response" in serializer.validated_data:
            guest.responded_at = (
                None if guest.response == "pending" else timezone.now()
            )
            guest.save(update_fields=["responded_at", "updated_at"])
        record_audit(
            event.business,
            None,
            "event_guest.organizer_updated",
            "event_guest",
            guest.public_id,
        )
        return Response(serialize_event_guest(guest, request, event))

    def delete(self, request, event_public_id, token, guest_public_id):
        event, guest = self.get_guest(event_public_id, token, guest_public_id)
        if not event or not guest:
            return event_access_denied()
        guest_id = guest.public_id
        guest.delete()
        record_audit(
            event.business,
            None,
            "event_guest.organizer_deleted",
            "event_guest",
            guest_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicEventOrganizerInviteLinkView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, event_public_id, token, guest_public_id):
        event = organizer_event(event_public_id, token)
        if not event:
            return event_access_denied()
        guest = get_object_or_404(
            EventGuest,
            event=event,
            public_id=guest_public_id,
        )
        serializer = EventInviteActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        should_send = serializer.validated_data["send_email"]
        if should_send and not guest.email:
            return Response(
                {
                    "error": {
                        "code": "INVITATION_EMAIL_REQUIRED",
                        "message": "Add an email address before sending this invitation.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invite_token = read_event_access_token(guest, "invite_token_digest")
        generated = serializer.validated_data["regenerate"] or not invite_token
        if generated:
            invite_token = issue_event_access_token(
                guest,
                "invite_token_digest",
            )
        if should_send:
            send_event_guest_invitation.delay(guest.pk, invite_token)
            guest.invite_sent_at = timezone.now()
            guest.save(update_fields=["invite_sent_at", "updated_at"])
        record_audit(
            event.business,
            None,
            (
                "event_guest.organizer_invitation_emailed"
                if should_send
                else "event_guest.organizer_invite_link_accessed"
            ),
            "event_guest",
            guest.public_id,
        )
        return Response(
            {
                "generated": generated,
                "sent": should_send,
                "invite_sent_at": guest.invite_sent_at,
                "token": invite_token,
            }
        )
