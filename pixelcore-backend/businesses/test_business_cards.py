import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Business, BusinessAsset, BusinessCard, BusinessMembership


User = get_user_model()


class BusinessCardApiTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_directory = tempfile.TemporaryDirectory(
            prefix="pixelcore-business-card-tests-"
        )
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        cls.media_directory.cleanup()

    def setUp(self):
        self.owner = User.objects.create_user(
            username="card-owner@example.com",
            email="card-owner@example.com",
            first_name="Ari",
            last_name="Santos",
            password="SafePassphrase123!",
        )
        self.colleague = User.objects.create_user(
            username="card-colleague@example.com",
            email="card-colleague@example.com",
            first_name="Mika",
            last_name="Reyes",
            password="SafePassphrase123!",
        )
        self.business = Business.objects.create(
            display_name="Fieldwork Studio",
            website_url="https://fieldwork.example.com",
            created_by=self.owner,
        )
        BusinessMembership.objects.create(
            business=self.business,
            user=self.owner,
            role="owner",
        )
        BusinessMembership.objects.create(
            business=self.business,
            user=self.colleague,
            role="staff",
        )

    def authenticate(self, user):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
        )

    def test_member_can_create_their_own_published_card(self):
        self.authenticate(self.owner)
        private_path = reverse(
            "member-business-card",
            kwargs={"public_id": self.business.public_id},
        )

        draft = self.client.get(private_path)
        self.assertEqual(draft.status_code, status.HTTP_200_OK)
        self.assertIsNone(draft.data["public_id"])
        self.assertEqual(draft.data["display_name"], "Ari Santos")
        self.assertEqual(draft.data["business_website_url"], "https://fieldwork.example.com")

        created = self.client.put(
            private_path,
            {
                "display_name": "Ari Santos",
                "job_title": "Founder",
                "headline": "Independent product and service studio",
                "email": "ari@example.com",
                "phone": "+63 917 555 0110",
                "style": "signature",
                "orientation": "landscape",
                "font_style": "editorial",
                "social_links": [
                    {
                        "platform": "linkedin",
                        "url": "https://www.linkedin.com/in/ari-santos",
                    }
                ],
                "show_social_links": True,
                "show_email": True,
                "show_phone": False,
                "show_business_address": False,
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertTrue(created.data["public_path"])

        public = self.client.get(
            reverse(
                "public-business-card",
                kwargs={"public_id": created.data["public_id"]},
            )
        )
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        self.assertEqual(public.data["email"], "ari@example.com")
        self.assertEqual(public.data["phone"], "")
        self.assertEqual(public.data["business_website_url"], "https://fieldwork.example.com")
        self.assertEqual(public.data["font_style"], "editorial")
        self.assertEqual(public.data["social_links"][0]["platform"], "linkedin")
        self.assertNotIn("show_email", public.data)
        self.assertNotIn("is_published", public.data)
        self.assertNotIn("show_social_links", public.data)
        self.assertNotIn("updated_at", public.data)

    def test_member_cannot_edit_another_members_card(self):
        card = BusinessCard.objects.create(
            business=self.business,
            user=self.owner,
            display_name="Ari Santos",
        )
        self.authenticate(self.colleague)

        response = self.client.put(
            reverse(
                "member-business-card",
                kwargs={"public_id": self.business.public_id},
            ),
            {"display_name": "Mika Reyes", "is_published": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        card.refresh_from_db()
        self.assertEqual(card.display_name, "Ari Santos")
        self.assertEqual(
            BusinessCard.objects.filter(business=self.business, user=self.colleague).count(),
            1,
        )

    def test_unpublished_card_is_not_public(self):
        card = BusinessCard.objects.create(
            business=self.business,
            user=self.owner,
            display_name="Ari Santos",
            is_published=False,
        )

        response = self.client.get(
            reverse("public-business-card", kwargs={"public_id": card.public_id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_can_upload_and_publish_an_image_background(self):
        self.authenticate(self.colleague)
        upload = self.client.post(
            reverse(
                "member-business-card-background",
                kwargs={"public_id": self.business.public_id},
            ),
            {
                "title": "Card texture",
                "file": SimpleUploadedFile(
                    "card-background.png",
                    b"pixelcore-card-background",
                    content_type="image/png",
                ),
            },
            format="multipart",
        )
        self.assertEqual(upload.status_code, status.HTTP_201_CREATED, upload.data)

        saved = self.client.put(
            reverse(
                "member-business-card",
                kwargs={"public_id": self.business.public_id},
            ),
            {
                "background_type": "image",
                "background_asset_public_id": upload.data["public_id"],
                "background_apply_to": "both",
                "background_image_fit": "cover",
                "background_image_position": "center",
                "background_overlay": "brand",
                "background_overlay_strength": "medium",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(saved.status_code, status.HTTP_201_CREATED, saved.data)
        self.assertTrue(saved.data["background_image_url"])

        public = self.client.get(
            reverse(
                "public-business-card",
                kwargs={"public_id": saved.data["public_id"]},
            )
        )
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        self.assertNotIn("background_asset_public_id", public.data)
        self.assertTrue(public.data["background_image_url"].startswith("/media/"))

    def test_public_card_uses_same_origin_logo_path(self):
        self.business.logo = SimpleUploadedFile(
            "business-logo.png",
            b"pixelcore-business-logo",
            content_type="image/png",
        )
        self.business.save(update_fields=["logo"])
        card = BusinessCard.objects.create(
            business=self.business,
            user=self.owner,
            display_name="Ari Santos",
            is_published=True,
        )

        response = self.client.get(
            reverse("public-business-card", kwargs={"public_id": card.public_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["logo_url"].startswith("/media/"))

    def test_member_cannot_select_another_business_background(self):
        other_business = Business.objects.create(
            display_name="Another Studio",
            created_by=self.owner,
        )
        foreign_asset = BusinessAsset.objects.create(
            business=other_business,
            uploaded_by=self.owner,
            title="Private background",
            asset_type="image",
            file=SimpleUploadedFile(
                "private.png",
                b"private-business-background",
                content_type="image/png",
            ),
            mime_type="image/png",
            size_bytes=27,
        )
        self.authenticate(self.colleague)

        response = self.client.put(
            reverse(
                "member-business-card",
                kwargs={"public_id": self.business.public_id},
            ),
            {
                "background_type": "image",
                "background_asset_public_id": str(foreign_asset.public_id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_social_profiles_require_unique_https_platforms(self):
        self.authenticate(self.owner)
        response = self.client.put(
            reverse(
                "member-business-card",
                kwargs={"public_id": self.business.public_id},
            ),
            {
                "social_links": [
                    {"platform": "instagram", "url": "http://instagram.com/ari"},
                    {"platform": "instagram", "url": "https://instagram.com/ari"},
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
