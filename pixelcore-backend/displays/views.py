from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.api import BusinessScopedModelViewSet
from businesses.services import device_from_token, record_audit
from catalog.models import Offering
from catalog.serializers import OfferingSerializer
from .models import DisplayDeviceAssignment, DisplayPublication
from .serializers import DisplayAssignmentSerializer, DisplayPublicationSerializer


class DisplayPublicationViewSet(BusinessScopedModelViewSet):
    queryset = DisplayPublication.objects.select_related("location", "background_asset")
    serializer_class = DisplayPublicationSerializer
    audit_resource = "display_publication"

    def perform_create(self, serializer):
        publication = serializer.save(business=self.get_business(), created_by=self.request.user)
        record_audit(publication.business, self.request.user, "display.created", "display_publication", publication.public_id)

    @action(detail=True, methods=["post"])
    def publish(self, request, business_public_id=None, public_id=None):
        publication = self.get_object(); publication.is_published = True; publication.published_at = timezone.now(); publication.save(update_fields=["is_published", "published_at", "updated_at"])
        record_audit(publication.business, request.user, "display.published", "display_publication", publication.public_id)
        return Response(self.get_serializer(publication).data)

    @action(detail=True, methods=["post"])
    def assign_device(self, request, business_public_id=None, public_id=None):
        publication = self.get_object(); serializer = DisplayAssignmentSerializer(data=request.data, context={"business": publication.business}); serializer.is_valid(raise_exception=True)
        device = serializer.validated_data["device_public_id"]
        DisplayDeviceAssignment.objects.update_or_create(device=device, defaults={"publication": publication})
        return Response({"device_public_id": str(device.public_id), "publication_public_id": str(publication.public_id)})


class PublicDisplayView(APIView):
    permission_classes = [AllowAny]; authentication_classes = []
    def get(self, request, share_key):
        publication = get_object_or_404(DisplayPublication.objects.select_related("business", "background_asset"), share_key=share_key, is_active=True, is_published=True, business__status="active")
        return Response(DisplayPublicationSerializer(publication, context={"business": publication.business, "request": request}).data)


class DisplayDeviceSessionView(APIView):
    permission_classes = [AllowAny]; authentication_classes = []
    def get(self, request):
        device = device_from_token(request.headers.get("X-Device-Token", ""), {"signage"})
        if not device: return Response({"error": {"code": "DEVICE_ACCESS_DENIED", "message": "Pair this display again.", "details": {}}}, status=403)
        assignment = DisplayDeviceAssignment.objects.select_related("publication", "publication__background_asset").filter(device=device, publication__is_active=True, publication__is_published=True).first()
        if not assignment: return Response({"device": {"name": device.name}, "publication": None})
        device.last_seen_at = timezone.now(); device.save(update_fields=["last_seen_at", "updated_at"])
        return Response({"device": {"name": device.name}, "publication": DisplayPublicationSerializer(assignment.publication, context={"business": device.business, "request": request}).data})
