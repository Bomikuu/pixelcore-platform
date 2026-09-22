from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_event_guest_invitation(guest_id, raw_token):
    from .models import EventGuest

    guest = EventGuest.objects.select_related("event", "event__business").get(
        pk=guest_id
    )
    event = guest.event
    invitation_url = (
        f"{settings.PIXELCORE_FRONTEND_URL.rstrip('/')}"
        f"/event/{event.public_id}/rsvp/{raw_token}"
    )
    try:
        event_zone = ZoneInfo(event.timezone)
    except ZoneInfoNotFoundError:
        event_zone = ZoneInfo("Asia/Manila")
    event_date = timezone.localtime(event.starts_at, event_zone).strftime(
        "%B %d, %Y at %I:%M %p"
    )
    send_mail(
        f"You're invited to {event.title}",
        (
            f"Hello {guest.full_name},\n\n"
            f"{event.organizer_name} invited you to {event.title} on {event_date}.\n\n"
            f"View the event and respond privately: {invitation_url}\n\n"
            "This link is unique to your invitation. Please do not forward it."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [guest.email],
    )
