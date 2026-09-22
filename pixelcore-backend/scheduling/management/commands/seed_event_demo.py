from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from businesses.models import Business, BusinessLocation
from scheduling.models import (
    EventGuest,
    EventMedia,
    EventParticipant,
    EventQuote,
    EventSchedule,
    EventStoryBlock,
    Resource,
    ResourceLayout,
    ResourceType,
    VenueEvent,
)
from scheduling.services import project_venue_event


DEMO_EVENT_TITLE = "Alex & Jamie's Garden Wedding"

DEMO_ELEMENTS = [
    {
        "name": "Sweetheart table",
        "element_type": "table",
        "capacity": 2,
        "shape": "rectangle",
        "width": 18,
        "height": 10,
        "position_x": 50,
        "position_y": 26,
        "is_bookable": True,
    },
    {
        "name": "Garden table 1",
        "element_type": "table",
        "capacity": 8,
        "shape": "round",
        "width": 16,
        "height": 16,
        "position_x": 24,
        "position_y": 55,
        "is_bookable": True,
    },
    {
        "name": "Garden table 2",
        "element_type": "table",
        "capacity": 8,
        "shape": "round",
        "width": 16,
        "height": 16,
        "position_x": 50,
        "position_y": 58,
        "is_bookable": True,
    },
    {
        "name": "Garden table 3",
        "element_type": "table",
        "capacity": 8,
        "shape": "round",
        "width": 16,
        "height": 16,
        "position_x": 76,
        "position_y": 55,
        "is_bookable": True,
    },
    {
        "name": "Ceremony stage",
        "element_type": "stage",
        "capacity": 1,
        "shape": "rectangle",
        "width": 34,
        "height": 12,
        "position_x": 50,
        "position_y": 10,
        "is_bookable": False,
    },
    {
        "name": "Dance floor",
        "element_type": "dance_floor",
        "capacity": 1,
        "shape": "square",
        "width": 24,
        "height": 24,
        "position_x": 50,
        "position_y": 84,
        "is_bookable": False,
    },
    {
        "name": "Reception entrance",
        "element_type": "entrance",
        "capacity": 1,
        "shape": "rectangle",
        "width": 16,
        "height": 8,
        "position_x": 10,
        "position_y": 12,
        "is_bookable": False,
    },
]

DEMO_GUESTS = [
    {
        "full_name": "Maya and Luis Santos",
        "email": "maya.santos@example.test",
        "party_size": 2,
        "response": "accepted",
        "table": "Garden table 1",
        "dietary_notes": "One vegetarian meal.",
        "guest_message": "May your home always feel as joyful as this garden does today.",
        "wish_approved": True,
    },
    {
        "full_name": "Noah Villanueva",
        "email": "noah.villanueva@example.test",
        "party_size": 1,
        "response": "accepted",
        "table": "Garden table 1",
        "guest_message": "Here is to slow mornings, brave adventures, and a lifetime of choosing each other.",
        "wish_approved": True,
    },
    {
        "full_name": "The Cruz family",
        "email": "cruz.family@example.test",
        "party_size": 4,
        "response": "accepted",
        "table": "Garden table 2",
        "dietary_notes": "High chair requested for one child.",
        "guest_message": "With all our love from the whole Cruz family.",
        "wish_approved": True,
    },
    {
        "full_name": "Isabel Garcia",
        "email": "isabel.garcia@example.test",
        "party_size": 2,
        "response": "maybe",
        "table": "Garden table 2",
    },
    {
        "full_name": "Paolo and Nina Reyes",
        "email": "reyes.party@example.test",
        "party_size": 2,
        "response": "pending",
        "table": "Garden table 3",
    },
    {
        "full_name": "Elena Mendoza",
        "email": "elena.mendoza@example.test",
        "party_size": 1,
        "response": "declined",
        "table": None,
        "guest_message": "Sending our warmest wishes from abroad.",
    },
    {
        "full_name": "The Lim household",
        "email": "lim.household@example.test",
        "party_size": 3,
        "response": "pending",
        "table": None,
    },
]


class Command(BaseCommand):
    help = "Create an idempotent wedding event with RSVP and seating demo data."

    def add_arguments(self, parser):
        parser.add_argument("--business-slug", default="northline-demo")
        parser.add_argument(
            "--event-id",
            help="Update an existing event by public UUID instead of resolving it by demo title.",
        )

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
                name="Main venue",
                code="main-venue",
                address=business.address,
                city=business.city,
                region=business.region,
                postal_code=business.postal_code,
                country=business.country or "PH",
                timezone=business.timezone or "Asia/Manila",
                is_primary=True,
                is_active=True,
            )
        if location.latitude is None and location.longitude is None:
            location.latitude = Decimal("14.554700")
            location.longitude = Decimal("121.024400")
            location.save(update_fields=["latitude", "longitude", "updated_at"])

        resource_type, _ = ResourceType.objects.get_or_create(
            business=business,
            name="Event seating",
            defaults={
                "singular_label": "Seat",
                "plural_label": "Seats",
                "icon": "armchair",
                "is_active": True,
            },
        )
        layout, _ = ResourceLayout.objects.update_or_create(
            business=business,
            location=location,
            name="Garden Pavilion Wedding Plan",
            defaults={
                "layout_type": "event",
                "description": "A reusable ceremony and reception layout with assigned guest tables.",
                "width": 100,
                "height": 100,
                "is_active": True,
            },
        )

        resources_by_name = {}
        for element in DEMO_ELEMENTS:
            name = element["name"]
            resource, _ = Resource.objects.update_or_create(
                business=business,
                location=location,
                name=name,
                defaults={
                    "resource_type": resource_type,
                    "layout": layout,
                    "is_active": True,
                    **{key: value for key, value in element.items() if key != "name"},
                },
            )
            resources_by_name[name] = resource

        try:
            event_zone = ZoneInfo(business.timezone or "Asia/Manila")
        except ZoneInfoNotFoundError:
            event_zone = ZoneInfo("Asia/Manila")

        event_defaults = {
            "event_type": "wedding",
            "status": "open",
            "starts_at": datetime(2026, 12, 12, 15, 0, tzinfo=event_zone),
            "ends_at": datetime(2026, 12, 12, 22, 0, tzinfo=event_zone),
            "timezone": str(event_zone),
            "location": location,
            "layout": layout,
            "organizer_name": "Alex Rivera",
            "organizer_email": "alex.rivera@example.test",
            "organizer_phone": "+63 917 555 0188",
            "description": (
                "A garden ceremony followed by dinner and dancing. "
                "Please respond for your full invited party."
            ),
            "public_rsvp_enabled": True,
            "website_enabled": True,
            "website_template": "wedding_editorial",
            "invitation_text": (
                "Together with their families, Alex and Jamie invite you to an intimate "
                "garden celebration shaped by good food, warm light, and the people they love."
            ),
            "closing_message": "Meet us in the garden",
            "hero_date_text": "121226",
            "countdown_enabled": True,
            "countdown_label": "Until we meet in the garden",
            "theme_background": "#080808",
            "theme_text": "#F5F1E8",
            "theme_accent": "#C8B99A",
            "heading_font": "Bodoni Moda",
            "body_font": "Manrope",
            "popup_enabled": True,
            "popup_title": "Welcome to the garden",
            "popup_message": (
                "We are so glad you are here. Enter to explore the day, find your venue details, "
                "and leave a note for Alex and Jamie."
            ),
            "popup_button_label": "Enter the celebration",
            "sections_config": {
                "event_detail": True,
                "participants": True,
                "story": True,
                "quote": True,
                "wish": True,
                "gallery": True,
            },
            "created_by": business.created_by,
        }

        requested_event_id = options.get("event_id")
        if requested_event_id:
            event = VenueEvent.objects.filter(
                business=business,
                public_id=requested_event_id,
            ).first()
            if not event:
                raise CommandError("The requested event was not found for this business.")
            for field, value in event_defaults.items():
                setattr(event, field, value)
            event.save(update_fields=[*event_defaults.keys(), "updated_at"])
            created = False
        else:
            event, created = VenueEvent.objects.update_or_create(
                business=business,
                title=DEMO_EVENT_TITLE,
                defaults=event_defaults,
            )

        for guest_data in DEMO_GUESTS:
            table_name = guest_data.get("table")
            EventGuest.objects.update_or_create(
                event=event,
                email=guest_data["email"],
                defaults={
                    "full_name": guest_data["full_name"],
                    "phone": guest_data.get("phone", ""),
                    "party_size": guest_data["party_size"],
                    "response": guest_data["response"],
                    "table": resources_by_name.get(table_name),
                    "dietary_notes": guest_data.get("dietary_notes", ""),
                    "guest_message": guest_data.get("guest_message", ""),
                    "wish_approved": guest_data.get("wish_approved", False),
                },
            )

        participants = [
            {
                "name": "Alex Rivera",
                "role": "Partner",
                "subtitle": "With the Rivera family",
                "family_text": "In loving memory of the ones who taught us how to build a generous life.",
            },
            {
                "name": "Jamie Flores",
                "role": "Partner",
                "subtitle": "With the Flores family",
                "family_text": "Surrounded by the family and friends who made every chapter possible.",
            },
        ]
        for sort_order, participant in enumerate(participants):
            EventParticipant.objects.update_or_create(
                event=event,
                sort_order=sort_order,
                defaults=participant,
            )

        event_address = ", ".join(
            part
            for part in [location.address, location.city, location.region]
            if part
        )
        schedule_entries = [
            {
                "title": "Garden ceremony",
                "starts_at": event.starts_at,
                "ends_at": event.starts_at.replace(hour=16, minute=0),
                "venue_name": "Garden Pavilion",
                "address": event_address,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "map_url": (
                    "https://www.google.com/maps/search/?api=1&query="
                    f"{location.latitude},{location.longitude}"
                ),
            },
            {
                "title": "Dinner and dancing",
                "starts_at": event.starts_at.replace(hour=17, minute=30),
                "ends_at": event.ends_at,
                "venue_name": "The Glass Hall",
                "address": event_address,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "map_url": (
                    "https://www.google.com/maps/search/?api=1&query="
                    f"{location.latitude},{location.longitude}"
                ),
            },
        ]
        for sort_order, entry in enumerate(schedule_entries):
            EventSchedule.objects.update_or_create(
                event=event,
                sort_order=sort_order,
                defaults=entry,
            )

        story_blocks = [
            {
                "date_label": "The first hello",
                "title": "One coffee, then another.",
                "body": (
                    "A quick introduction became an entire afternoon, and neither of us was ready "
                    "for the conversation to end."
                ),
            },
            {
                "date_label": "The years between",
                "title": "A thousand ordinary days.",
                "body": (
                    "Home arrived slowly: shared playlists, long drives, Sunday groceries, and the "
                    "steady joy of becoming a team."
                ),
            },
            {
                "date_label": "This chapter",
                "title": "Meet us in the garden.",
                "body": (
                    "We are gathering the people who shaped us to begin the next part of our story "
                    "with dinner, dancing, and a promise."
                ),
            },
        ]
        for sort_order, block in enumerate(story_blocks):
            EventStoryBlock.objects.update_or_create(
                event=event,
                sort_order=sort_order,
                defaults=block,
            )

        asset_root = Path(__file__).resolve().parents[2] / "demo_assets" / "event"
        generated_media = [
            (
                "popup",
                "garden-welcome.png",
                "A candlelit garden pavilion prepared to welcome wedding guests.",
            ),
            (
                "closing",
                "garden-closing.png",
                "Two chairs beneath warm lanterns on a quiet garden path at dusk.",
            ),
        ]
        for placement, filename, alt_text in generated_media:
            asset_path = asset_root / filename
            if not asset_path.exists() or event.media.filter(placement=placement).exists():
                continue
            media = EventMedia(
                event=event,
                placement=placement,
                alt_text=alt_text,
                is_featured=True,
            )
            with asset_path.open("rb") as asset_file:
                media.image.save(filename, File(asset_file), save=False)
            media.save()

        story_media = event.media.filter(placement="story").order_by(
            "sort_order",
            "id",
        ).first()
        first_story = event.story_blocks.order_by("sort_order", "id").first()
        if story_media and first_story and not first_story.image_id:
            first_story.image = story_media
            first_story.save(update_fields=["image"])

        EventQuote.objects.update_or_create(
            event=event,
            defaults={
                "is_enabled": True,
                "original_text": "To be known completely, and still chosen—this is the quiet promise we make.",
                "translation": "",
                "citation": "For this day and every day after",
            },
        )

        project_venue_event(event, business.created_by)
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} {event.title} for {business.slug}: "
                f"{event.guests.count()} invited parties across "
                f"{layout.resources.filter(element_type__in=('table', 'booth')).count()} tables."
            )
        )
        self.stdout.write(
            "Open Workspace > Schedule > Events & RSVP, then generate links from the event controls."
        )
