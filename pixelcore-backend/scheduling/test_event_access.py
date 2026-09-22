from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from businesses.models import Business, BusinessLocation, BusinessMembership
from catalog.models import Offering
from .models import (
    EventGuest,
    Resource,
    ResourceLayout,
    ResourceType,
    StaffProfile,
    VenueEvent,
)


class VenueEventAccessApiTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="event-owner@example.com",
            email="event-owner@example.com",
            password="SafePassphrase123!",
        )
        self.business = Business.objects.create(
            display_name="Event Studio",
            created_by=self.owner,
        )
        BusinessMembership.objects.create(
            business=self.business,
            user=self.owner,
            role="owner",
        )
        self.location = BusinessLocation.objects.create(
            business=self.business,
            name="Garden Hall",
            code="garden-hall",
            timezone="Asia/Manila",
        )
        self.event = VenueEvent.objects.create(
            business=self.business,
            title="Alex and Jamie's Wedding",
            starts_at=timezone.now() + timedelta(days=30),
            location=self.location,
            organizer_name="Alex Rivera",
            max_guests=12,
            created_by=self.owner,
        )
        token = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def organizer_link_url(self):
        return (
            f"/api/businesses/{self.business.public_id}/venue-events/"
            f"{self.event.public_id}/organizer-link/"
        )

    def guest_link_url(self, guest):
        return (
            f"/api/businesses/{self.business.public_id}/venue-events/"
            f"{self.event.public_id}/guests/{guest.public_id}/invite-link/"
        )

    def event_url(self):
        return (
            f"/api/businesses/{self.business.public_id}/venue-events/"
            f"{self.event.public_id}/"
        )

    def guest_collection_url(self):
        return f"{self.event_url()}guests/"

    def test_guest_collection_paginates_and_keeps_event_wide_seating_summary(self):
        layout = ResourceLayout.objects.create(
            business=self.business,
            location=self.location,
            name="Wedding reception",
            layout_type="event",
        )
        resource_type = ResourceType.objects.create(
            business=self.business,
            name="Guest tables",
            singular_label="Table",
            plural_label="Tables",
        )
        garden_table = Resource.objects.create(
            business=self.business,
            resource_type=resource_type,
            location=self.location,
            layout=layout,
            name="Garden table 1",
            element_type="table",
            capacity=8,
        )
        self.event.layout = layout
        self.event.save(update_fields=["layout", "updated_at"])

        for index in range(25):
            EventGuest.objects.create(
                event=self.event,
                full_name=f"Guest {index + 1:02d}",
                email=f"guest-{index + 1}@example.com",
                party_size=2 if index < 2 else 1,
                response="declined" if index == 1 else "pending",
                table=garden_table if index < 2 else None,
            )

        response = self.client.get(
            self.guest_collection_url(),
            {"page": 2, "page_size": 10, "table": "unassigned"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 23)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["page_size"], 10)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertTrue(all(guest["table_public_id"] is None for guest in response.data["results"]))
        self.assertEqual(response.data["summary"]["total"], 25)
        self.assertEqual(response.data["summary"]["unassigned"], 23)
        self.assertEqual(response.data["summary"]["tables"][0]["name"], "Garden table 1")
        self.assertEqual(response.data["summary"]["tables"][0]["guest_count"], 2)
        self.assertEqual(response.data["summary"]["tables"][0]["assigned_seats"], 2)
        self.assertEqual(
            response.data["summary"]["tables"][0]["guest_names"],
            ["Guest 01", "Guest 02"],
        )

    def test_guest_collection_without_list_parameters_keeps_legacy_array_shape(self):
        EventGuest.objects.create(
            event=self.event,
            full_name="Legacy guest",
            email="legacy@example.com",
        )

        response = self.client.get(self.guest_collection_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(response.data[0]["full_name"], "Legacy guest")

    def test_event_handler_and_products_are_business_scoped(self):
        handler = StaffProfile.objects.create(
            business=self.business,
            display_name="Morgan Santos",
            job_title="Event coordinator",
        )
        team_member = StaffProfile.objects.create(
            business=self.business,
            display_name="Jamie Cruz",
            job_title="Venue lead",
        )
        product = Offering.objects.create(
            business=self.business,
            name="Wedding coordination",
            offering_type="physical",
            status="published",
        )

        saved = self.client.patch(
            self.event_url(),
            {
                "handler_public_id": str(handler.public_id),
                "assigned_staff_public_ids": [str(team_member.public_id)],
                "product_public_ids": [str(product.public_id)],
            },
            format="json",
        )

        self.assertEqual(saved.status_code, status.HTTP_200_OK)
        self.assertEqual(saved.data["handler_name"], "Morgan Santos")
        self.assertCountEqual(
            [str(staff_id) for staff_id in saved.data["assigned_staff_public_ids"]],
            [str(handler.public_id), str(team_member.public_id)],
        )
        self.assertEqual(
            [str(product_id) for product_id in saved.data["product_public_ids"]],
            [str(product.public_id)],
        )

        other_business = Business.objects.create(
            display_name="Other Events",
            created_by=self.owner,
        )
        other_handler = StaffProfile.objects.create(
            business=other_business,
            display_name="Outside Handler",
        )
        other_product = Offering.objects.create(
            business=other_business,
            name="Outside package",
            offering_type="physical",
            status="published",
        )

        rejected = self.client.patch(
            self.event_url(),
            {
                "handler_public_id": str(other_handler.public_id),
                "assigned_staff_public_ids": [str(other_handler.public_id)],
                "product_public_ids": [str(other_product.public_id)],
            },
            format="json",
        )

        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)

    def test_organizer_link_is_retrievable_until_explicitly_replaced(self):
        empty = self.client.get(self.organizer_link_url())
        created = self.client.post(self.organizer_link_url(), {}, format="json")
        current = self.client.get(self.organizer_link_url())
        reused = self.client.post(self.organizer_link_url(), {}, format="json")
        replaced = self.client.post(
            self.organizer_link_url(),
            {"regenerate": True},
            format="json",
        )

        self.assertEqual(empty.status_code, status.HTTP_200_OK)
        self.assertFalse(empty.data["has_link"])
        self.assertEqual(created.status_code, status.HTTP_200_OK)
        self.assertEqual(current.data["token"], created.data["token"])
        self.assertEqual(reused.data["token"], created.data["token"])
        self.assertNotEqual(replaced.data["token"], created.data["token"])

    @patch("scheduling.views.send_event_guest_invitation.delay")
    def test_guest_invite_can_be_emailed_without_rotating_its_link(self, send_delay):
        guest = EventGuest.objects.create(
            event=self.event,
            full_name="Sam Rivera",
            email="sam@example.com",
            party_size=2,
        )
        copied = self.client.post(self.guest_link_url(guest), {}, format="json")
        emailed = self.client.post(
            self.guest_link_url(guest),
            {"send_email": True},
            format="json",
        )

        self.assertEqual(emailed.status_code, status.HTTP_200_OK)
        self.assertEqual(emailed.data["token"], copied.data["token"])
        self.assertTrue(emailed.data["sent"])
        send_delay.assert_called_once_with(guest.pk, copied.data["token"])

    def test_confirmations_cannot_exceed_event_capacity(self):
        EventGuest.objects.create(
            event=self.event,
            full_name="First household",
            email="first@example.com",
            party_size=10,
            response="accepted",
        )
        guest = EventGuest.objects.create(
            event=self.event,
            full_name="Second household",
            email="second@example.com",
            party_size=3,
        )
        response = self.client.patch(
            (
                f"/api/businesses/{self.business.public_id}/venue-events/"
                f"{self.event.public_id}/guests/{guest.public_id}/"
            ),
            {"response": "accepted"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("party_size", response.data["error"]["details"])
