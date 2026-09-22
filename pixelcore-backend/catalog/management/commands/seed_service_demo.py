from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from businesses.models import Business, BusinessLocation
from catalog.models import Category, Offering
from scheduling.models import (
    AvailabilityRule,
    SchedulingSettings,
    ServiceAssignment,
    StaffProfile,
)


DEMO_SERVICES = [
    {
        "name": "Personal shopping appointment",
        "slug": "personal-shopping-appointment",
        "summary": "A focused one-to-one session for product selection, sizing, and recommendations.",
        "description": (
            "Meet with a product specialist for guided selection, sizing support, "
            "and practical recommendations based on your needs."
        ),
        "base_price": Decimal("750.00"),
        "duration_minutes": 45,
        "capacity": 2,
    },
    {
        "name": "Venue walkthrough",
        "slug": "venue-walkthrough",
        "summary": "Review the venue, floor plan, guest flow, and setup options with the team.",
        "description": (
            "A guided walkthrough for celebrations, launches, meetings, and private events. "
            "The team will review layouts, access, guest capacity, and service areas."
        ),
        "base_price": Decimal("500.00"),
        "duration_minutes": 60,
        "capacity": 8,
    },
    {
        "name": "Event planning consultation",
        "slug": "event-planning-consultation",
        "summary": "Plan the schedule, venue layout, suppliers, and guest experience for an upcoming event.",
        "description": (
            "A structured planning session covering timelines, floor-plan needs, "
            "service areas, suppliers, and the next decisions required for your event."
        ),
        "base_price": Decimal("1500.00"),
        "duration_minutes": 90,
        "capacity": 6,
    },
]


class Command(BaseCommand):
    help = "Create idempotent published demo services with staff availability."

    def add_arguments(self, parser):
        parser.add_argument("--business-slug", default="northline-demo")

    @transaction.atomic
    def handle(self, *args, **options):
        business = Business.objects.filter(
            slug=options["business_slug"],
            status="active",
        ).first()
        if not business:
            raise CommandError("An active business with that slug was not found.")

        location = business.locations.filter(is_active=True).first()
        if not location:
            location = BusinessLocation.objects.create(
                business=business,
                name="Main location",
                code="main",
                city=business.city,
                region=business.region,
                country=business.country or "PH",
                timezone=business.timezone or "Asia/Manila",
                is_primary=True,
                is_active=True,
            )

        staff = StaffProfile.objects.filter(
            business=business,
            is_active=True,
            is_bookable=True,
        ).first()
        if not staff:
            staff = StaffProfile.objects.create(
                business=business,
                display_name="Demo booking host",
                job_title="Customer experience host",
                employment_status="active",
                timezone=business.timezone or "Asia/Manila",
                is_bookable=True,
                is_active=True,
            )

        category, _ = Category.objects.get_or_create(
            business=business,
            slug="services",
            defaults={
                "name": "Services",
                "description": "Appointments and venue services available to book.",
                "show_in_header": False,
                "is_active": True,
            },
        )

        created_count = 0
        updated_count = 0
        for service_data in DEMO_SERVICES:
            service, created = Offering.objects.update_or_create(
                business=business,
                slug=service_data["slug"],
                defaults={
                    "category": category,
                    "name": service_data["name"],
                    "summary": service_data["summary"],
                    "description": service_data["description"],
                    "offering_type": "service",
                    "status": "published",
                    "fulfillment_type": "booking",
                    "base_price": service_data["base_price"],
                    "compare_at_price": None,
                    "tax_rate": Decimal("0.000"),
                    "sku": "",
                    "track_inventory": False,
                    "duration_minutes": service_data["duration_minutes"],
                    "capacity": service_data["capacity"],
                    "metadata": {"booking_payment_policy": "none", "demo_record": True},
                },
            )
            created_count += int(created)
            updated_count += int(not created)
            ServiceAssignment.objects.update_or_create(
                business=business,
                staff=staff,
                offering=service,
                location=location,
                defaults={"is_active": True},
            )

        for weekday in range(6):
            AvailabilityRule.objects.get_or_create(
                business=business,
                staff=staff,
                location=location,
                weekday=weekday,
                starts_at=time(9, 0),
                ends_at=time(17, 0),
                defaults={"is_active": True},
            )

        SchedulingSettings.objects.update_or_create(
            business=business,
            defaults={
                "public_booking_enabled": True,
                "public_intro": (
                    "Choose a service and request a time. The team will confirm the details with you."
                ),
                "advance_booking_days": 31,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded services for {business.slug}: "
                f"{created_count} created, {updated_count} updated, "
                f"assigned to {staff.display_name}."
            )
        )
