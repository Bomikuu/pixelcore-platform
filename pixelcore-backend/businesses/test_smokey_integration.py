from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework.test import APITestCase
from .models import Business, BusinessCapability, BusinessMembership, BusinessDevice


class SmokeyIntegrationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="module-owner")
        self.business = Business.objects.create(display_name="Module shop", created_by=self.user)
        self.member = BusinessMembership.objects.create(business=self.business, user=self.user, role="owner")
        self.url = f"/api/businesses/{self.business.public_id}/smokey-integration/"
        self.client.force_authenticate(self.user)

    def test_disabled_business_descriptor_has_no_private_settings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["installed"])
        self.assertFalse(response.data["enabled"])
        self.assertIn("configure", response.data["permissions"])
        self.assertNotIn("default_connection_id", response.data)

    def test_missing_package_does_not_import_optional_models(self):
        with patch("businesses.smokey_integration.package_installed", return_value=False):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["installed"])
        self.assertFalse(response.data["enabled"])

    def test_manager_and_active_capability(self):
        BusinessCapability.objects.create(business=self.business, code="smokey", status="active")
        self.member.role = "manager"
        self.member.save()
        response = self.client.get(self.url)
        self.assertTrue(response.data["enabled"])
        self.assertNotIn("configure", response.data["permissions"])
        self.assertNotIn("delete_reports", response.data["permissions"])

    def test_staff_nonmember_and_unauthenticated_are_denied(self):
        self.member.role = "staff"
        self.member.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.member.delete()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_other_business_and_inactive_business_are_denied(self):
        other = Business.objects.create(display_name="Other shop", created_by=self.user)
        self.assertEqual(self.client.get(f"/api/businesses/{other.public_id}/smokey-integration/").status_code, 404)
        self.business.status = "suspended"
        self.business.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_device_credentials_do_not_authorize_private_module(self):
        device = BusinessDevice.objects.create(business=self.business, created_by=self.user, name="Fixture terminal", device_type="attendance")
        token = signing.dumps({"device": str(device.public_id), "version": device.token_version}, salt="pixelcore.device-session", compress=True)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url, HTTP_X_DEVICE_TOKEN=token).status_code, 401)

    def test_inactive_membership_is_denied(self):
        self.member.status = "inactive"
        self.member.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
