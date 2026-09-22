import base64
from datetime import timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from businesses.models import Business, BusinessMembership
from .models import EventGuest, EventMedia, VenueEvent
from .services import issue_event_access_token


class EventWebsiteApiTests(APITestCase):
    PNG_BYTES = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="wedding-owner@example.com",
            email="wedding-owner@example.com",
            password="SafePassphrase123!",
        )
        self.business = Business.objects.create(
            display_name="Northline Events",
            created_by=self.owner,
        )
        BusinessMembership.objects.create(
            business=self.business,
            user=self.owner,
            role="owner",
        )
        self.event = VenueEvent.objects.create(
            business=self.business,
            title="Alex and Jamie",
            event_type="wedding",
            status="open",
            starts_at=timezone.now() + timedelta(days=60),
            organizer_name="Alex Rivera",
            created_by=self.owner,
        )
        token = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @property
    def workspace_url(self):
        return (
            f"/api/businesses/{self.business.public_id}/venue-events/"
            f"{self.event.public_id}/website/"
        )

    @property
    def public_url(self):
        return f"/api/public/events/{self.event.public_id}/website/"

    def test_website_is_private_until_published(self):
        response = self.client.get(self.public_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_editor_atomically_saves_wedding_content(self):
        response = self.client.patch(
            self.workspace_url,
            {
                "website_enabled": True,
                "invitation_text": "Join us for an evening together.",
                "hero_date_text": "120926",
                "participants": [
                    {
                        "name": "Alex Rivera",
                        "role": "Partner",
                        "subtitle": "Celebrating with",
                        "family_text": "The Rivera family",
                        "sort_order": 0,
                    },
                    {
                        "name": "Jamie Cruz",
                        "role": "Partner",
                        "subtitle": "Celebrating with",
                        "family_text": "The Cruz family",
                        "sort_order": 1,
                    },
                ],
                "schedule_entries": [
                    {
                        "title": "Ceremony",
                        "starts_at": self.event.starts_at.isoformat(),
                        "ends_at": (self.event.starts_at + timedelta(hours=1)).isoformat(),
                        "venue_name": "Garden Hall",
                        "address": "Makati, Metro Manila",
                        "sort_order": 0,
                    }
                ],
                "story_blocks": [
                    {
                        "title": "How we met",
                        "body": "A shared route became a life together.",
                        "date_label": "2022",
                        "sort_order": 0,
                    }
                ],
                "quote": {
                    "is_enabled": True,
                    "original_text": "A quiet promise.",
                    "translation": "A life composed together.",
                    "citation": "Our vows",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["website_enabled"])
        self.assertIsNotNone(response.data["website_published_at"])
        self.assertEqual(len(response.data["participants"]), 2)
        self.assertEqual(len(response.data["schedule_entries"]), 1)
        self.assertEqual(response.data["quote"]["citation"], "Our vows")

    def test_public_payload_only_includes_approved_guest_wishes(self):
        self.event.website_enabled = True
        self.event.website_published_at = timezone.now()
        self.event.save(update_fields=["website_enabled", "website_published_at"])
        EventGuest.objects.create(
            event=self.event,
            full_name="Approved guest",
            email="approved@example.com",
            guest_message="Wishing you a joyful life together.",
            wish_approved=True,
        )
        EventGuest.objects.create(
            event=self.event,
            full_name="Private guest",
            email="private@example.com",
            guest_message="This stays private.",
            wish_approved=False,
        )
        self.client.credentials()

        response = self.client.get(self.public_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wishes = response.data["event"]["website"]["approved_wishes"]
        self.assertEqual(wishes, [{"name": "Approved guest", "message": "Wishing you a joyful life together."}])

    def test_private_invitation_payload_personalizes_the_same_website(self):
        guest = EventGuest.objects.create(
            event=self.event,
            full_name="Taylor and family",
            email="taylor@example.com",
        )
        invite_token = issue_event_access_token(guest, "invite_token_digest")
        self.client.credentials()

        response = self.client.get(
            f"/api/public/events/{self.event.public_id}/rsvp/{invite_token}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["guest"]["full_name"], "Taylor and family")
        self.assertEqual(response.data["event"]["website"]["website_template"], "wedding_editorial")

    def test_event_type_limits_the_available_template_family(self):
        accepted = self.client.patch(
            self.workspace_url,
            {
                "event_type": "birthday",
                "website_template": "birthday_color",
                "popup_enabled": True,
                "popup_title": "Come celebrate",
                "popup_message": "A birthday evening with our favorite people.",
                "popup_button_label": "Open the party",
                "countdown_enabled": True,
                "countdown_label": "Until the candles are lit",
            },
            format="json",
        )

        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data["event_type"], "birthday")
        self.assertEqual(accepted.data["website_template"], "birthday_color")
        self.assertTrue(accepted.data["popup_enabled"])
        self.assertTrue(accepted.data["countdown_enabled"])
        self.assertEqual(accepted.data["countdown_label"], "Until the candles are lit")

        rejected = self.client.patch(
            self.workspace_url,
            {"website_template": "wedding_garden"},
            format="json",
        )

        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)

    def test_background_music_upload_is_validated_and_tenant_scoped(self):
        music_url = f"{self.workspace_url}music/"
        upload = SimpleUploadedFile(
            "event-theme.mp3",
            b"ID3" + (b"\x00" * 64),
            content_type="audio/mpeg",
        )

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                music_url,
                {"file": upload, "title": "Entrance theme"},
                format="multipart",
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data["music_enabled"])
            self.assertEqual(response.data["background_music_title"], "Entrance theme")
            self.assertIn("/media/businesses/", response.data["background_music_url"])

    def test_event_images_have_single_slots_and_story_assignments(self):
        media_url = f"{self.workspace_url}media/"

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            for filename in ("first-hero.png", "replacement-hero.png"):
                response = self.client.post(
                    media_url,
                    {
                        "image": SimpleUploadedFile(
                            filename,
                            self.PNG_BYTES,
                            content_type="image/png",
                        ),
                        "placement": "hero",
                        "alt_text": "Event hero",
                    },
                    format="multipart",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            self.assertEqual(
                EventMedia.objects.filter(event=self.event, placement="hero").count(),
                1,
            )

            story_media = self.client.post(
                media_url,
                {
                    "image": SimpleUploadedFile(
                        "story.png",
                        self.PNG_BYTES,
                        content_type="image/png",
                    ),
                    "placement": "story",
                    "alt_text": "A shared afternoon",
                },
                format="multipart",
            )
            self.assertEqual(story_media.status_code, status.HTTP_201_CREATED)

            response = self.client.patch(
                self.workspace_url,
                {
                    "story_blocks": [
                        {
                            "title": "How we met",
                            "body": "One coffee became an entire afternoon.",
                            "image_public_id": story_media.data["public_id"],
                            "sort_order": 0,
                        }
                    ]
                },
                format="json",
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                str(response.data["story_blocks"][0]["image_public_id"]),
                str(story_media.data["public_id"]),
            )
            self.assertIn("/media/businesses/", response.data["story_blocks"][0]["image_url"])

    def test_editor_saves_rsvp_dress_code_and_event_note_settings(self):
        deadline = self.event.starts_at - timedelta(days=14)
        sections = {
            "event_detail": True,
            "participants": True,
            "story": True,
            "quote": True,
            "wish": True,
            "gallery": True,
            "order": [
                "hero",
                "event_detail",
                "participants",
                "story",
                "quote",
                "wish",
                "gallery",
            ],
            "rsvp": {
                "heading": "Kindly respond",
                "subtitle": "We hope you can join us.",
                "deadline": deadline.isoformat(),
                "submit_label": "Send our response",
                "accept_label": "Joyfully accept",
                "decline_label": "Regretfully decline",
                "allow_maybe": True,
                "show_party_size": True,
                "show_dietary_notes": True,
                "show_guest_message": True,
                "max_party_size": 6,
                "attending_title": "We cannot wait",
                "attending_message": "Your place is waiting.",
                "declining_title": "Thank you for letting us know",
                "declining_message": "You will be missed.",
            },
            "dress_code": {
                "enabled": True,
                "heading": "Garden formal",
                "subtitle": "Soft colors and natural textures",
                "description": "Choose comfortable shoes for the lawn.",
                "colors": ["#d7c7a3", "#284c3f"],
                "media_public_id": None,
            },
            "event_notes": {
                "enabled": True,
                "heading": "Before you arrive",
                "subtitle": "A few thoughtful details",
                "items": [
                    {
                        "icon": "car",
                        "title": "Parking",
                        "body": "Valet service begins at three in the afternoon.",
                    }
                ],
            },
        }

        response = self.client.patch(
            self.workspace_url,
            {"sections_config": sections},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sections_config"]["rsvp"]["max_party_size"], 6)
        self.assertTrue(response.data["sections_config"]["rsvp"]["allow_maybe"])
        self.assertEqual(
            response.data["sections_config"]["dress_code"]["colors"],
            ["#D7C7A3", "#284C3F"],
        )
        self.assertIsNone(response.data["sections_config"]["dress_code"]["media_url"])
        self.assertEqual(
            response.data["sections_config"]["event_notes"]["items"][0]["title"],
            "Parking",
        )

    def test_editor_rejects_invalid_nested_rsvp_settings(self):
        base = {
            "event_detail": True,
            "participants": True,
            "story": True,
            "quote": True,
            "wish": True,
            "gallery": True,
            "order": ["hero", "event_detail", "participants", "story", "quote", "wish", "gallery"],
        }
        invalid_configs = [
            {"rsvp": {"deadline": "not-a-date"}},
            {"rsvp": {"max_party_size": 0}},
            {"dress_code": {"colors": ["green"]}},
            {"dress_code": {"colors": ["#123456"] * 9}},
            {"event_notes": {"items": [{"icon": "info", "title": "", "body": ""}]}},
            {
                "event_notes": {
                    "items": [
                        {"icon": "info", "title": f"Note {index}", "body": ""}
                        for index in range(9)
                    ]
                }
            },
        ]

        for config in invalid_configs:
            with self.subTest(config=config):
                response = self.client.patch(
                    self.workspace_url,
                    {"sections_config": {**base, **config}},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dress_code_image_must_belong_to_the_same_event(self):
        other_event = VenueEvent.objects.create(
            business=self.business,
            title="Another celebration",
            event_type="wedding",
            status="open",
            starts_at=timezone.now() + timedelta(days=90),
            organizer_name="Another organizer",
            created_by=self.owner,
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            other_image = EventMedia.objects.create(
                event=other_event,
                image=SimpleUploadedFile(
                    "other-event.png",
                    self.PNG_BYTES,
                    content_type="image/png",
                ),
                placement="gallery",
                alt_text="Another event",
            )
            response = self.client.patch(
                self.workspace_url,
                {
                    "sections_config": {
                        **self.event.sections_config,
                        "dress_code": {
                            "enabled": True,
                            "heading": "Garden formal",
                            "media_public_id": str(other_image.public_id),
                        },
                    }
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_rsvp_respects_configured_deadline(self):
        guest = EventGuest.objects.create(
            event=self.event,
            full_name="Deadline guest",
            email="deadline@example.com",
        )
        token = issue_event_access_token(guest, "invite_token_digest")
        self.client.credentials()
        endpoint = f"/api/public/events/{self.event.public_id}/rsvp/{token}/"

        self.event.sections_config = {
            **self.event.sections_config,
            "rsvp": {"deadline": (timezone.now() - timedelta(minutes=1)).isoformat()},
        }
        self.event.save(update_fields=["sections_config"])
        closed = self.client.patch(
            endpoint,
            {"response": "accepted", "party_size": 1},
            format="json",
        )

        self.assertEqual(closed.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(closed.data["error"]["code"], "RSVP_CLOSED")

        self.event.sections_config = {
            **self.event.sections_config,
            "rsvp": {
                "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                "max_party_size": 2,
                "allow_maybe": False,
            },
        }
        self.event.save(update_fields=["sections_config"])
        accepted = self.client.patch(
            endpoint,
            {"response": "accepted", "party_size": 2},
            format="json",
        )

        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data["guest"]["response"], "accepted")
        self.assertEqual(accepted.data["guest"]["party_size"], 2)
