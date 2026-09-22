import base64
import hashlib
import secrets
from datetime import timedelta
from urllib.parse import quote, urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core import signing
from django.utils import timezone

from .models import GoogleCalendarConnection


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"
GOOGLE_STATE_SALT = "pixelcore.google-calendar"


class GoogleCalendarError(Exception):
    pass


def google_calendar_is_configured():
    return bool(
        settings.GOOGLE_CALENDAR_CLIENT_ID
        and settings.GOOGLE_CALENDAR_CLIENT_SECRET
        and settings.GOOGLE_CALENDAR_REDIRECT_URI
    )


def _fernet():
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_token(value):
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8") if value else ""


def decrypt_token(value):
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise GoogleCalendarError("Stored Google credentials could not be read. Reconnect Google Calendar.") from exc


def build_google_authorization_url(user, business):
    if not google_calendar_is_configured():
        raise GoogleCalendarError("Google Calendar is not configured on this server.")
    state = signing.dumps(
        {"user_id": user.id, "business_id": business.id, "nonce": secrets.token_urlsafe(18)},
        salt=GOOGLE_STATE_SALT,
        compress=True,
    )
    query = urlencode(
        {
            "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "response_type": "code",
            "scope": f"openid email {GOOGLE_CALENDAR_SCOPE}",
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def decode_google_state(state):
    try:
        return signing.loads(state, salt=GOOGLE_STATE_SALT, max_age=10 * 60)
    except signing.BadSignature as exc:
        raise GoogleCalendarError("The Google Calendar connection request expired. Please try again.") from exc


def _response_payload(response):
    try:
        return response.json()
    except ValueError:
        return {}


def exchange_authorization_code(code):
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
            "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    payload = _response_payload(response)
    if not response.ok or not payload.get("access_token"):
        raise GoogleCalendarError(payload.get("error_description") or "Google did not return an access token.")
    return payload


def save_google_connection(business, user, token_payload):
    existing = GoogleCalendarConnection.objects.filter(business=business).first()
    refresh_token = token_payload.get("refresh_token")
    if not refresh_token and existing:
        refresh_token = decrypt_token(existing.encrypted_refresh_token)
    if not refresh_token:
        raise GoogleCalendarError("Google did not return offline access. Reconnect and approve Calendar access.")
    connection, _ = GoogleCalendarConnection.objects.update_or_create(
        business=business,
        defaults={
            "connected_by": user,
            "google_email": user.email,
            "calendar_id": "primary",
            "encrypted_access_token": encrypt_token(token_payload["access_token"]),
            "encrypted_refresh_token": encrypt_token(refresh_token),
            "token_expiry": timezone.now() + timedelta(seconds=max(60, int(token_payload.get("expires_in") or 3600))),
            "scopes": token_payload.get("scope", GOOGLE_CALENDAR_SCOPE),
            "is_active": True,
            "last_error": "",
        },
    )
    return connection


def _refresh_access_token(connection):
    refresh_token = decrypt_token(connection.encrypted_refresh_token)
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
            "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    payload = _response_payload(response)
    if not response.ok or not payload.get("access_token"):
        connection.is_active = False
        connection.last_error = (payload.get("error_description") or "Google access expired. Reconnect Calendar.")[:500]
        connection.save(update_fields=["is_active", "last_error", "updated_at"])
        raise GoogleCalendarError(connection.last_error)
    connection.encrypted_access_token = encrypt_token(payload["access_token"])
    connection.token_expiry = timezone.now() + timedelta(seconds=max(60, int(payload.get("expires_in") or 3600)))
    connection.is_active = True
    connection.last_error = ""
    connection.save(update_fields=["encrypted_access_token", "token_expiry", "is_active", "last_error", "updated_at"])
    return payload["access_token"]


def _access_token(connection, force_refresh=False):
    expires_soon = not connection.token_expiry or connection.token_expiry <= timezone.now() + timedelta(minutes=1)
    if force_refresh or expires_soon:
        return _refresh_access_token(connection)
    return decrypt_token(connection.encrypted_access_token)


def _calendar_request(connection, method, path, payload=None, retry=True):
    token = _access_token(connection)
    response = requests.request(
        method,
        f"{GOOGLE_CALENDAR_API}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        json=payload,
        timeout=15,
    )
    if response.status_code == 401 and retry:
        token = _access_token(connection, force_refresh=True)
        response = requests.request(
            method,
            f"{GOOGLE_CALENDAR_API}{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            json=payload,
            timeout=15,
        )
    response_payload = _response_payload(response)
    if not response.ok and response.status_code not in (404, 410):
        detail = response_payload.get("error", {})
        if isinstance(detail, dict):
            detail = detail.get("message")
        raise GoogleCalendarError(str(detail or "Google Calendar could not be updated."))
    return response, response_payload


def _google_event_id(event):
    raw = f"pixelcore:{event.business_id}:business-event:{event.id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _event_payload(event):
    end = event.ends_at or (event.starts_at + timedelta(hours=1))
    description = "\n\n".join(
        part for part in [event.notes.strip(), f"PixelCore type: {event.get_event_type_display()}", f"Business: {event.business.display_name}"] if part
    )
    return {
        "summary": f"[Cancelled] {event.title}" if event.status == "cancelled" else event.title,
        "description": description,
        "start": {"dateTime": event.starts_at.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "extendedProperties": {
            "private": {"pixelcore_event_id": str(event.id), "pixelcore_business_id": str(event.business.public_id)}
        },
        "reminders": {"useDefault": True},
    }


def sync_calendar_event(event, connection=None):
    connection = connection or GoogleCalendarConnection.objects.filter(business=event.business, is_active=True).first()
    if not connection:
        event.google_sync_status = "not_connected"
        event.google_sync_error = ""
        event.save(update_fields=["google_sync_status", "google_sync_error", "updated_at"])
        return False
    event.google_sync_status = "pending"
    event.google_sync_error = ""
    event.save(update_fields=["google_sync_status", "google_sync_error", "updated_at"])
    try:
        calendar_id = quote(connection.calendar_id or "primary", safe="")
        event_id = event.google_event_id or _google_event_id(event)
        path = f"/calendars/{calendar_id}/events/{quote(event_id, safe='')}"
        response, payload = _calendar_request(connection, "PATCH", path, _event_payload(event))
        if response.status_code in (404, 410):
            response, payload = _calendar_request(
                connection,
                "POST",
                f"/calendars/{calendar_id}/events",
                {"id": event_id, **_event_payload(event)},
            )
        event.google_event_id = payload.get("id", event_id)
        event.google_calendar_id = connection.calendar_id or "primary"
        event.google_event_url = payload.get("htmlLink", event.google_event_url)
        event.google_sync_status = "synced"
        event.google_synced_at = timezone.now()
        event.google_sync_error = ""
        event.save(update_fields=["google_event_id", "google_calendar_id", "google_event_url", "google_sync_status", "google_synced_at", "google_sync_error", "updated_at"])
        return True
    except (GoogleCalendarError, requests.RequestException) as exc:
        event.google_sync_status = "error"
        event.google_sync_error = str(exc)[:500]
        event.save(update_fields=["google_sync_status", "google_sync_error", "updated_at"])
        return False


def delete_google_event(event):
    if not event.google_event_id:
        return True
    connection = GoogleCalendarConnection.objects.filter(business=event.business, is_active=True).first()
    if not connection:
        return False
    try:
        calendar_id = quote(event.google_calendar_id or connection.calendar_id or "primary", safe="")
        event_id = quote(event.google_event_id, safe="")
        _calendar_request(connection, "DELETE", f"/calendars/{calendar_id}/events/{event_id}")
        return True
    except (GoogleCalendarError, requests.RequestException):
        return False
