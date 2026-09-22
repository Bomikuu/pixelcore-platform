from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from businesses.models import Business
from catalog.models import Offering
from businesses.models import BusinessLocation
from .models import AvailabilityRule, Resource, ResourceType, ServiceAssignment, StaffProfile
from .services import BookingConflict, create_booking


class BookingConcurrencyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="North Star Studio", created_by=self.user)
        self.offering = Offering.objects.create(business=self.business, name="Consultation", offering_type="service", duration_minutes=60, base_price="500.00")
        self.staff = StaffProfile.objects.create(business=self.business, display_name="Casey")
        ServiceAssignment.objects.create(business=self.business, offering=self.offering, staff=self.staff)

    def test_prevents_overlapping_staff_booking_and_projects_event(self):
        starts_at = timezone.now() + timedelta(days=1)
        data = {"offering": self.offering, "staff": self.staff, "starts_at": starts_at, "ends_at": starts_at + timedelta(hours=1), "timezone": "Asia/Manila", "email": "first@example.com", "payment_policy": "none"}
        booking, _ = create_booking(self.business, dict(data), self.user)
        self.assertIsNotNone(booking.event_id)

        conflicting = dict(data, email="second@example.com")
        with self.assertRaises(BookingConflict):
            create_booking(self.business, conflicting, self.user)

    def test_resource_collision_is_enforced(self):
        location = BusinessLocation.objects.create(business=self.business, name="Main", code="main", timezone="Asia/Manila")
        resource_type = ResourceType.objects.create(business=self.business, name="Room", singular_label="Room", plural_label="Rooms")
        resource = Resource.objects.create(business=self.business, resource_type=resource_type, location=location, name="Room A", capacity=4)
        starts_at = timezone.now() + timedelta(days=2)
        data = {"offering": self.offering, "staff": self.staff, "resources": [resource], "location": location, "starts_at": starts_at, "ends_at": starts_at + timedelta(hours=1), "timezone": "Asia/Manila", "email": "one@example.com", "payment_policy": "none"}
        create_booking(self.business, dict(data), self.user)
        second_staff = StaffProfile.objects.create(business=self.business, display_name="Jordan")
        with self.assertRaises(BookingConflict):
            create_booking(self.business, {**data, "staff": second_staff, "email": "two@example.com"}, self.user)
