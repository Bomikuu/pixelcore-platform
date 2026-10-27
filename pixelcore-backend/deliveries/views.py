import secrets

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.models import Business, BusinessMembership
from businesses.services import record_audit
from businesses.views import member_business
from commerce.models import Order
from commerce.services import token_digest
from .models import Delivery, DeliveryEvent, RiderAccess
from .payloads import delivery_payload, rider_payload
from .serializers import DeliveryMutation, LocationInput, RiderInput
from .services import (TERMINAL, check_revision, clear_location, coordinates, locked_delivery,
                       receive_location, rider_access_query, rider_is_active, transition, verified_email)


def deliveries():
    return Delivery.objects.select_related("order__business", "order__customer", "order__cart", "rider__business", "rider__user").prefetch_related("events", "order__items")


def validated(serializer_class, request):
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class PrivateResponse(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class OwnerDeliveries(PrivateResponse):
    def get(self, request, business_public_id):
        business = member_business(request.user, business_public_id, roles=("owner", "admin", "manager"))
        rows = deliveries().filter(order__business=business)
        summary = dict(rows.values("stage").annotate(total=Count("id")).values_list("stage", "total"))
        stage = request.query_params.get("stage", "active")
        if stage == "active":
            rows = rows.exclude(stage__in=TERMINAL)
        elif stage != "all":
            if stage not in dict(Delivery.STAGES):
                raise ValidationError({"stage": "Choose a supported delivery status."})
            rows = rows.filter(stage=stage)
        paginator = PageNumberPagination()
        paginator.page_size = 30
        page = paginator.paginate_queryset(rows, request)
        return Response({"count": paginator.page.paginator.count, "next": paginator.get_next_link(), "previous": paginator.get_previous_link(), "results": [delivery_payload(d) for d in page], "riders": [rider_payload(r) for r in business.delivery_riders.select_related("user", "business")], "summary": summary, "refreshed_at": timezone.now()})


class OwnerDelivery(PrivateResponse):
    @transaction.atomic
    def patch(self, request, business_public_id, public_id):
        business = member_business(request.user, business_public_id, roles=("owner", "admin", "manager"))
        Business.objects.select_for_update().get(pk=business.pk)
        row = locked_delivery(public_id, deliveries().filter(order__business=business))
        data = validated(DeliveryMutation, request)
        check_revision(row, data["revision"])
        action = data["action"]
        if action == "assign":
            rider = get_object_or_404(RiderAccess.objects.select_for_update(of=("self",)).select_related("user", "business"), business=business, public_id=data["rider_id"]) if data["rider_id"] else None
            if rider and not rider_is_active(rider):
                raise ValidationError({"rider_id": "This rider must accept access and be active before assignment."})
            row.rider = rider
            clear_location(row)
            if row.stage == "out_for_delivery":
                row.stage = "ready"
            row.revision += 1
            row.save()
            DeliveryEvent.objects.create(delivery=row, stage=row.stage, message="Rider assigned" if rider else "Rider unassigned")
        elif action == "destination":
            if data["latitude"] is None and data["longitude"] is None:
                row.destination_latitude = row.destination_longitude = None
            else:
                row.destination_latitude, row.destination_longitude = coordinates(data["latitude"], data["longitude"])
            row.revision += 1
            row.save()
        elif action == "stage":
            transition(row, data["stage"], request.user)
        else:
            raise ValidationError({"action": "Only the assigned rider can control location sharing."})
        record_audit(business, request.user, f"delivery.{action}", "delivery", row.public_id)
        row.refresh_from_db()
        return Response(delivery_payload(deliveries().get(pk=row.pk)))


class OwnerRiders(PrivateResponse):
    @transaction.atomic
    def post(self, request, business_public_id):
        business = member_business(request.user, business_public_id, roles=("owner", "admin", "manager"))
        Business.objects.select_for_update().get(pk=business.pk)
        data = validated(RiderInput, request)
        email = data["email"].strip().lower()
        user = None
        if data["kind"] == "employee":
            user = get_user_model().objects.filter(email__iexact=email, is_active=True, business_memberships__business=business, business_memberships__status="active").first()
            if not user:
                raise ValidationError({"email": "Choose the email of an active employee account in this business."})
        existing = RiderAccess.objects.select_for_update().filter(business=business, email=email).first()
        if existing and existing.status != "revoked":
            raise ValidationError({"email": "This rider already has access or an invitation."})
        rider = existing or RiderAccess(business=business, email=email)
        rider.display_name, rider.kind, rider.user = data["display_name"], data["kind"], user
        rider.status = "active" if user else "invited"
        rider.save()
        record_audit(business, request.user, "delivery_rider.added", "rider", rider.public_id)
        return Response(rider_payload(rider), status=201)


class OwnerRider(PrivateResponse):
    @transaction.atomic
    def delete(self, request, business_public_id, public_id):
        business = member_business(request.user, business_public_id, roles=("owner", "admin", "manager"))
        Business.objects.select_for_update().get(pk=business.pk)
        rider = get_object_or_404(RiderAccess, business=business, public_id=public_id)
        # All writers lock the order first. Lock grants last to avoid inversion with assignment.
        ids = list(Delivery.objects.filter(rider=rider).values_list("order_id", flat=True))
        list(Order.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
        rider = RiderAccess.objects.select_for_update().get(pk=rider.pk)
        rider.status = "revoked"
        rider.save(update_fields=["status"])
        for row in Delivery.objects.select_for_update().filter(rider=rider):
            clear_location(row)
            row.rider = None
            if row.stage == "out_for_delivery":
                row.stage = "ready"
            row.revision += 1
            row.save()
        record_audit(business, request.user, "delivery_rider.revoked", "rider", rider.public_id)
        return Response(status=204)


class RiderDeliveries(PrivateResponse):
    def get(self, request):
        grants = list(rider_access_query(request.user).exclude(status="revoked"))
        active_ids = [r.pk for r in grants if rider_is_active(r)]
        rows = deliveries().filter(rider_id__in=active_ids).exclude(stage__in=TERMINAL)
        return Response({"results": [delivery_payload(d, "rider") for d in rows], "invitations": [rider_payload(r) for r in grants if r.status == "invited"], "businesses": [rider_payload(r) for r in grants if r.pk in active_ids], "refreshed_at": timezone.now()})


class RiderAccept(PrivateResponse):
    @transaction.atomic
    def post(self, request, public_id):
        email = verified_email(request.user)
        if not email:
            raise PermissionDenied("Verify your account email before accepting rider access.")
        grant = get_object_or_404(RiderAccess.objects.select_for_update(), public_id=public_id, email=email, kind="independent", status="invited", business__status="active")
        grant.user, grant.status = request.user, "active"
        grant.save(update_fields=["user", "status"])
        record_audit(grant.business, request.user, "delivery_rider.accepted", "rider", grant.public_id)
        return Response(rider_payload(grant))


def rider_scope(user):
    active_ids = [r.pk for r in rider_access_query(user) if rider_is_active(r)]
    return deliveries().filter(rider_id__in=active_ids, rider__user=user, rider__status="active")


class RiderDelivery(PrivateResponse):
    @transaction.atomic
    def patch(self, request, public_id):
        row = locked_delivery(public_id, rider_scope(request.user))
        # Check again after acquiring locks (a suspended employee cannot retain a cached grant).
        if not rider_is_active(row.rider):
            raise PermissionDenied("Your delivery access is no longer active.")
        data = validated(DeliveryMutation, request)
        check_revision(row, data["revision"])
        if data["action"] == "stage" and data["stage"] in {"out_for_delivery", "delivered"}:
            transition(row, data["stage"], request.user)
        elif data["action"] == "sharing":
            if row.stage != "out_for_delivery":
                raise ValidationError({"sharing": "Start the delivery before sharing your location."})
            if not data["sharing"]:
                clear_location(row)
            else:
                row.sharing = True
            row.save()
        else:
            raise PermissionDenied("Riders can start or complete assigned deliveries and control their own location sharing.")
        row.refresh_from_db()
        return Response(delivery_payload(deliveries().get(pk=row.pk), "rider"))


class RiderLocation(PrivateResponse):
    @transaction.atomic
    def post(self, request, public_id):
        row = locked_delivery(public_id, rider_scope(request.user))
        if not rider_is_active(row.rider):
            raise PermissionDenied("Your delivery access is no longer active.")
        data = validated(LocationInput, request)
        check_revision(row, data["revision"])
        accepted = receive_location(row, data)
        return Response({"accepted": accepted, "refresh_after": 30, "received_at": row.received_at})


class CustomerTracking(PrivateResponse):
    permission_classes = [AllowAny]

    def get(self, request, slug, order_id):
        business = get_object_or_404(Business, slug=slug, status="active")
        row = get_object_or_404(deliveries(), order__business=business, order__public_id=order_id)
        order = row.order
        owns = request.user.is_authenticated and order.customer_id and order.customer.user_id == request.user.id
        token = request.headers.get("X-Cart-Token", "")
        guest = bool(token and order.cart_id and secrets.compare_digest(order.cart.access_token_digest, token_digest(token)))
        if not owns and not guest:
            raise PermissionDenied("Sign in to the account that placed this order or use its original checkout device.")
        return Response({"delivery": delivery_payload(row, "customer"), "refreshed_at": timezone.now()})
