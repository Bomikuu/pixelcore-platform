from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.http import Http404
from smokey_assistant.contracts import AssistantError
from .models import (
    Business,
    BusinessMembership,
    BusinessCapability,
    default_modules,
    supported_modules,
)
from .smokey_bridge import context_for


class SmokeyAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="smokey-owner")
        self.business = Business.objects.create(
            display_name="Assistant business", created_by=self.user
        )
        self.member = BusinessMembership.objects.create(
            user=self.user, business=self.business, role="owner"
        )

    def test_install_does_not_enable_module(self):
        self.assertIn("smokey", supported_modules())
        self.assertNotIn("smokey", default_modules())
        with self.assertRaises(PermissionDenied):
            context_for(self.user, self.business.public_id, "generate")

    def test_roles_and_disabled_capability_are_enforced(self):
        capability = BusinessCapability.objects.create(
            business=self.business, code="smokey", status="active"
        )
        self.assertIn(
            "configure",
            context_for(self.user, self.business.public_id, "configure").permissions,
        )
        self.member.role = "manager"
        self.member.save()
        with self.assertRaises(AssistantError):
            context_for(self.user, self.business.public_id, "configure")
        context_for(self.user, self.business.public_id, "generate")
        capability.status = "disabled"
        capability.save()
        with self.assertRaises(PermissionDenied):
            context_for(self.user, self.business.public_id, "generate")

    def test_staff_and_cross_business_access_are_denied(self):
        BusinessCapability.objects.create(
            business=self.business, code="smokey", status="active"
        )
        self.member.role = "staff"
        self.member.save()
        with self.assertRaises(Http404):
            context_for(self.user, self.business.public_id, "generate")
