from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import hashlib
from tempfile import TemporaryDirectory

from .identity import default_identity_config
from .models import AccountProfile, Business, BusinessAsset, BusinessDevice, BusinessInvitation, BusinessMembership
from .services import issue_account_challenge


User = get_user_model()


class BusinessAssetApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="asset-owner@example.com",
            email="asset-owner@example.com",
            password="SafePassphrase123!",
        )
        self.business = Business.objects.create(display_name="Asset Studio", created_by=self.owner)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.owner).access_token}")

    def test_upload_accepts_tenant_asset_path_longer_than_one_hundred_characters(self):
        upload = SimpleUploadedFile(
            "58429d58a6515b1e0ad75ae8_lmfeaea.png",
            b"\x89PNG\r\n\x1a\n",
            content_type="image/png",
        )

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("business-assets", kwargs={"public_id": self.business.public_id}),
                {"title": "Product image", "asset_type": "image", "file": upload},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        asset = BusinessAsset.objects.get(public_id=response.data["public_id"])
        self.assertGreater(len(asset.file.name), 100)
        self.assertEqual(BusinessAsset._meta.get_field("file").max_length, 500)


class BusinessIdentityApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner@example.com", email="owner@example.com", password="SafePassphrase123!")
        self.outsider = User.objects.create_user(username="other@example.com", email="other@example.com", password="SafePassphrase123!")
        self.business = Business.objects.create(
            display_name="North Star Studio",
            legal_name="North Star Studio Incorporated",
            contact_email="hello@example.com",
            created_by=self.owner,
        )
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    def test_public_identity_excludes_legal_name(self):
        response = self.client.get(
            reverse("public-business-identity", kwargs={"slug": self.business.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["display_name"], "North Star Studio")
        self.assertNotIn("legal_name", response.data)

    def test_outsider_cannot_read_private_business(self):
        self.authenticate(self.outsider)

        response = self.client.get(
            reverse("business-detail", kwargs={"public_id": self.business.public_id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_valid_branding(self):
        self.authenticate(self.owner)

        response = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"primary_color": "#2255AA"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["branding"]["primary_color"], "#2255AA")

    def test_owner_can_select_storefront_mode_and_invalid_modes_are_rejected(self):
        self.authenticate(self.owner)

        response = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"storefront": {"mode": "luxury"}}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["branding"]["storefront"]["mode"], "luxury")

    def test_owner_can_select_marketplace_storefront_layout(self):
        self.authenticate(self.owner)
        response = self.client.patch(
            f"/api/businesses/{self.business.public_id}/identity/",
            {"branding": {"storefront": {"layout": "marketplace"}}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["branding"]["storefront"]["layout"],
            "marketplace",
        )

        rejected = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"storefront": {"mode": "custom-script"}}},
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rejected.data["error"]["code"], "VALIDATION_ERROR")

    def test_unknown_branding_key_is_rejected(self):
        self.authenticate(self.owner)

        response = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"script": "<script>alert(1)</script>"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")

    def test_owner_can_update_centralized_identity_configuration(self):
        self.authenticate(self.owner)
        branding = default_identity_config()
        branding["typography"]["heading_font"] = "Manrope"
        branding["style"]["card_radius"] = "medium"
        branding["storefront"]["hero"].update({
            "enabled": True,
            "heading": "Equipment for the everyday route",
            "type": "gradient",
        })
        branding["socials"] = [{"platform": "instagram", "url": "https://instagram.com/example"}]

        response = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": branding},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["branding"]["schema_version"], 1)
        self.assertEqual(response.data["branding"]["storefront"]["hero"]["heading"], "Equipment for the everyday route")
        self.assertEqual(response.data["branding"]["font_family"], "Manrope")
        self.assertIn("branding_defaults", response.data)

    def test_custom_markup_is_sanitized_and_executable_css_is_rejected(self):
        self.authenticate(self.owner)
        safe_response = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"advanced": {"custom_html": '<p class="intro">Hello<script>alert(1)</script></p>', "custom_css": ".intro { font-weight: 700; }"}}},
            format="json",
        )
        self.assertEqual(safe_response.status_code, status.HTTP_200_OK)
        self.assertEqual(safe_response.data["branding"]["advanced"]["custom_html"], '<p class="intro">Hello</p>')

        rejected = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"advanced": {"custom_css": '@import url("https://example.com/a.css");'}}},
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rejected.data["error"]["code"], "VALIDATION_ERROR")

    def test_malformed_identity_types_return_validation_errors(self):
        self.authenticate(self.owner)
        response = self.client.patch(
            reverse("business-identity", kwargs={"public_id": self.business.public_id}),
            {"branding": {"storefront": {"hero": {"enabled": "yes", "gradient_angle": "sideways"}}}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")

    def test_public_identity_resolves_only_referenced_business_assets(self):
        asset = BusinessAsset.objects.create(
            business=self.business,
            title="Hero visual",
            asset_type="image",
            file=SimpleUploadedFile("hero.png", b"\x89PNG\r\n\x1a\n", content_type="image/png"),
            mime_type="image/png",
            size_bytes=8,
            uploaded_by=self.owner,
        )
        branding = default_identity_config()
        branding["storefront"]["hero"]["asset_id"] = str(asset.public_id)
        self.business.branding = branding
        self.business.save(update_fields=["branding"])

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.get(reverse("public-business-identity", kwargs={"slug": self.business.slug}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["branding_assets"][str(asset.public_id)]["asset_type"], "image")


class RegistrationApiTests(APITestCase):
    @patch("businesses.views.send_account_code.delay")
    def test_registration_verification_and_onboarding_are_account_first(self, send_code):
        response = self.client.post(
            reverse("register"),
            {
                "email": "founder@example.com",
                "password": "SafePassphrase123!",
                "password_confirm": "SafePassphrase123!",
                "first_name": "Casey",
                "last_name": "Founder",
                "phone": "+639171234567",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(BusinessMembership.objects.exists())
        user = User.objects.get(email="founder@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(AccountProfile.objects.get(user=user).phone, "+639171234567")
        _, code = issue_account_challenge(user, "verify_email")
        verified = self.client.post(reverse("verify-email"), {"email": user.email, "code": code}, format="json")
        self.assertEqual(verified.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {verified.data['access']}")
        onboarded = self.client.post(
            reverse("business-onboarding"),
            {"display_name": "Casey & Company", "country": "PH", "location_name": "Makati", "industry_preset": "restaurant", "enabled_modules": ["site", "sell", "schedule", "operate"]},
            format="json",
        )
        self.assertEqual(onboarded.status_code, status.HTTP_201_CREATED)
        membership = BusinessMembership.objects.select_related("business", "user").get()
        self.assertEqual(membership.role, "owner")
        self.assertEqual(membership.business.display_name, "Casey & Company")
        self.assertEqual(membership.business.industry_preset, "restaurant")
        self.assertEqual(membership.user.email, "founder@example.com")

    def test_login_accepts_phone_identifier(self):
        user = User.objects.create_user(username="casey", email="casey@example.com", password="SafePassphrase123!")
        AccountProfile.objects.create(user=user, phone="+639181234567")
        response = self.client.post(reverse("login"), {"identifier": "+639181234567", "password": "SafePassphrase123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_blacklisted_refresh_token_returns_unauthorized(self):
        user = User.objects.create_user(username="expired", email="expired@example.com", password="SafePassphrase123!")
        refresh = RefreshToken.for_user(user)
        refresh.blacklist()
        self.client.cookies[settings.PIXELCORE_REFRESH_COOKIE] = str(refresh)

        response = self.client.post(reverse("refresh"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "REFRESH_INVALID")


class BusinessEventApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner@example.com", email="owner@example.com", password="SafePassphrase123!")
        self.outsider = User.objects.create_user(username="outsider@example.com", email="outsider@example.com", password="SafePassphrase123!")
        self.business = Business.objects.create(display_name="North Star Studio", created_by=self.owner)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    def test_member_can_create_generic_event(self):
        self.authenticate(self.owner)
        starts_at = timezone.now()

        response = self.client.post(
            reverse("business-events", kwargs={"public_id": self.business.public_id}),
            {
                "title": "Quarterly planning",
                "event_type": "meeting",
                "starts_at": starts_at.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Quarterly planning")
        self.assertEqual(response.data["google_sync_status"], "not_connected")

    def test_outsider_cannot_list_events(self):
        self.authenticate(self.outsider)

        response = self.client.get(
            reverse("business-events", kwargs={"public_id": self.business.public_id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TeamInvitationTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="team-owner", email="team-owner@example.com", password="SafePassphrase123!")
        self.invitee = User.objects.create_user(username="new-staff", email="new-staff@example.com", password="SafePassphrase123!")
        self.business = Business.objects.create(display_name="Team Studio", created_by=self.owner)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")
        self.authenticate(self.owner)

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    @patch("businesses.views.send_team_invitation.delay")
    def test_invitation_is_emailed_without_exposing_token_and_acceptance_links_staff(self, send_invitation):
        with self.captureOnCommitCallbacks(execute=True):
            created = self.client.post(reverse("business-invitations", kwargs={"public_id": self.business.public_id}), {"email": self.invitee.email, "role": "staff"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertNotIn("acceptance_token", created.data)
        invitation_id, raw_token = send_invitation.call_args.args
        invitation = BusinessInvitation.objects.get(pk=invitation_id)
        self.assertEqual(invitation.token_digest, hashlib.sha256(raw_token.encode()).hexdigest())
        self.authenticate(self.invitee)
        accepted = self.client.post(reverse("business-invitation-accept"), {"token": raw_token}, format="json")
        self.assertEqual(accepted.status_code, 200)
        membership = BusinessMembership.objects.get(business=self.business, user=self.invitee)
        self.assertEqual(membership.staff_profile.email, self.invitee.email)
        self.assertEqual(membership.staff_profile.employment_status, "pending")

    def test_device_link_rejects_cross_tenant_display(self):
        other = Business.objects.create(display_name="Other Studio", created_by=self.invitee)
        station = BusinessDevice.objects.create(business=self.business, name="Station", device_type="pos", created_by=self.owner)
        display = BusinessDevice.objects.create(business=other, name="Display", device_type="customer_display", created_by=self.invitee)
        response = self.client.post(
            reverse("business-device-links", kwargs={"business_public_id": self.business.public_id}),
            {"source_device_public_id": str(station.public_id), "target_device_public_id": str(display.public_id)},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_owner_can_create_customer_display_without_a_location(self):
        response = self.client.post(
            reverse("business-devices", kwargs={"business_public_id": self.business.public_id}),
            {
                "name": "Front customer screen",
                "device_type": "customer_display",
                "location_public_id": None,
                "configuration": {},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["device_type"], "customer_display")
        self.assertIsNone(response.data["location_public_id"])
