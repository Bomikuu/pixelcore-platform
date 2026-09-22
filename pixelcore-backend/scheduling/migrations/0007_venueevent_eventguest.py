import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("businesses", "0019_location_coordinates_and_event_layout"),
        ("scheduling", "0006_venue_layout_and_scheduling_settings"),
    ]

    operations = [
        migrations.CreateModel(
            name="VenueEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(max_length=180)),
                ("event_type", models.CharField(choices=[("wedding", "Wedding"), ("private_event", "Private event"), ("corporate", "Corporate event"), ("community", "Community event"), ("other", "Other event")], default="private_event", max_length=24)),
                ("status", models.CharField(choices=[("planning", "Planning"), ("open", "RSVP open"), ("closed", "RSVP closed"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="planning", max_length=16)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("timezone", models.CharField(default="Asia/Manila", max_length=64)),
                ("organizer_name", models.CharField(max_length=160)),
                ("organizer_email", models.EmailField(blank=True, max_length=254)),
                ("organizer_phone", models.CharField(blank=True, max_length=32)),
                ("description", models.TextField(blank=True, max_length=4000)),
                ("public_rsvp_enabled", models.BooleanField(default=True)),
                ("organizer_token_digest", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="venue_events", to="businesses.business")),
                ("calendar_event", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="venue_event", to="businesses.businessevent")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_venue_events", to=settings.AUTH_USER_MODEL)),
                ("layout", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="venue_events", to="scheduling.resourcelayout")),
                ("location", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="venue_events", to="businesses.businesslocation")),
            ],
            options={"ordering": ["starts_at", "id"]},
        ),
        migrations.CreateModel(
            name="EventGuest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("full_name", models.CharField(max_length=160)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("party_size", models.PositiveSmallIntegerField(default=1)),
                ("response", models.CharField(choices=[("pending", "Awaiting reply"), ("accepted", "Attending"), ("declined", "Not attending"), ("maybe", "Maybe")], default="pending", max_length=16)),
                ("dietary_notes", models.CharField(blank=True, max_length=500)),
                ("guest_message", models.CharField(blank=True, max_length=1000)),
                ("invite_token_digest", models.CharField(blank=True, max_length=64)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guests", to="scheduling.venueevent")),
                ("table", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="event_guests", to="scheduling.resource")),
            ],
            options={"ordering": ["full_name", "id"]},
        ),
    ]
