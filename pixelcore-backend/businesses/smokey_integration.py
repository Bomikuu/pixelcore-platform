"""Optional frontend-module descriptor; safe without importing Smokey models."""
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import BusinessMembership


def package_installed():
    return "smokey_assistant" in settings.INSTALLED_APPS


class SmokeyIntegrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        member = get_object_or_404(
            BusinessMembership.objects.select_related("business"),
            business__public_id=public_id,
            business__status="active",
            user=request.user,
            status="active",
            role__in=("owner", "admin", "manager"),
        )
        installed = package_installed()
        permissions = ["generate", "view_reports"]
        if member.role in ("owner", "admin"):
            permissions += ["configure", "delete_reports"]
        response = Response({
            "installed": installed,
            "enabled": installed and member.business.capabilities.filter(code="smokey", status="active").exists(),
            "hostApiVersion": {"major": 1, "minor": 0},
            "permissions": permissions,
            "reportKinds": ["daily", "sales", "attendance", "late"] if installed else [],
        })
        response["Cache-Control"] = "private, no-store"
        return response
