import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from django.conf import settings
from django.core import signing

from .models import AccountChallenge, AuditEvent, BusinessCapability, BusinessDevice, BusinessInvitation, BusinessLocation, default_modules
from .google_calendar import decrypt_token, encrypt_token


@transaction.atomic
def bootstrap_business(business):
    for code in default_modules():
        BusinessCapability.objects.get_or_create(business=business, code=code)

    location, _ = BusinessLocation.objects.get_or_create(
        business=business,
        code="main",
        defaults={
            "name": "Main location",
            "address": business.address,
            "city": business.city,
            "region": business.region,
            "postal_code": business.postal_code,
            "country": business.country,
            "timezone": business.timezone,
            "is_primary": True,
        },
    )
    if business.industry_preset == "restaurant":
        from scheduling.models import ResourceLayout, ResourceType
        ResourceType.objects.get_or_create(
            business=business,
            name="Table",
            defaults={"singular_label": "Table", "plural_label": "Tables", "icon": "utensils"},
        )
        ResourceLayout.objects.get_or_create(
            business=business,
            location=location,
            name="Main floor",
        )
    sync_enabled_modules(business)
    return business


def sync_enabled_modules(business):
    enabled = list(
        business.capabilities.exclude(status="disabled").order_by("code").values_list("code", flat=True)
    )
    if business.enabled_modules != enabled:
        business.enabled_modules = enabled
        business.save(update_fields=["enabled_modules", "updated_at"])
    return enabled


@transaction.atomic
def set_capabilities(business, codes, actor=None):
    normalized = set(codes)
    from .models import supported_modules
    for code in supported_modules():
        capability, _ = BusinessCapability.objects.get_or_create(business=business, code=code)
        target = "active" if code in normalized else "disabled"
        if capability.status != target:
            capability.status = target
            capability.save(update_fields=["status", "updated_at"])
    sync_enabled_modules(business)
    record_audit(business, actor, "capabilities.updated", "business", business.public_id, {"enabled": sorted(normalized)})


def create_invitation(business, email, role, actor, lifetime_days=7):
    raw_token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    invitation = BusinessInvitation.objects.create(
        business=business,
        email=email.lower().strip(),
        role=role,
        token_digest=digest,
        invited_by=actor,
        expires_at=timezone.now() + timedelta(days=lifetime_days),
    )
    record_audit(business, actor, "team.invited", "business_invitation", invitation.public_id, {"email": invitation.email})
    return invitation, raw_token


def unique_location_code(business, name):
    base = slugify(name)[:60] or "location"
    candidate = base
    suffix = 2
    while business.locations.filter(code=candidate).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def record_audit(business, actor, action, resource_type, resource_id="", metadata=None):
    return AuditEvent.objects.create(
        business=business,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id or ""),
        metadata=metadata or {},
    )


def account_code_digest(user, purpose, code):
    return signing.salted_hmac(
        "pixelcore.account-challenge",
        f"{user.pk}:{purpose}:{str(code).strip()}",
        secret=settings.SECRET_KEY,
    ).hexdigest()


@transaction.atomic
def issue_account_challenge(user, purpose):
    AccountChallenge.objects.filter(user=user, purpose=purpose, consumed_at__isnull=True).update(
        consumed_at=timezone.now()
    )
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = AccountChallenge.objects.create(
        user=user,
        purpose=purpose,
        code_digest=account_code_digest(user, purpose, code),
    )
    return challenge, code


@transaction.atomic
def consume_account_challenge(user, purpose, code):
    challenge = (
        AccountChallenge.objects.select_for_update()
        .filter(user=user, purpose=purpose, consumed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if challenge is None or not challenge.is_usable:
        return False
    challenge.attempts += 1
    if not secrets.compare_digest(challenge.code_digest, account_code_digest(user, purpose, code)):
        challenge.save(update_fields=["attempts"])
        return False
    challenge.consumed_at = timezone.now()
    challenge.save(update_fields=["attempts", "consumed_at"])
    return True


def device_code_digest(code):
    return signing.salted_hmac("pixelcore.device-pairing", str(code).strip().upper(), secret=settings.SECRET_KEY).hexdigest()


def issue_device_pairing_code(device):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(alphabet) for _ in range(8))
    device.pairing_code_digest = device_code_digest(code)
    device.pairing_code_encrypted = encrypt_token(code)
    device.pairing_code_issued_at = timezone.now()
    device.token_version += 1
    device.save(update_fields=["pairing_code_digest", "pairing_code_encrypted", "pairing_code_issued_at", "token_version", "updated_at"])
    return code


def current_device_pairing_code(device):
    if not device.pairing_code_digest or not device.pairing_code_encrypted:
        return ""
    return decrypt_token(device.pairing_code_encrypted)


@transaction.atomic
def pair_device(code, device_types=None):
    digest = device_code_digest(code)
    queryset = BusinessDevice.objects.select_for_update().filter(
        pairing_code_digest=digest,
        is_active=True,
    )
    if device_types:
        queryset = queryset.filter(device_type__in=device_types)
    device = queryset.first()
    if not device:
        return None, None
    device.pairing_code_digest = ""
    device.pairing_code_encrypted = ""
    device.pairing_code_issued_at = None
    device.last_seen_at = timezone.now()
    device.save(update_fields=["pairing_code_digest", "pairing_code_encrypted", "pairing_code_issued_at", "last_seen_at", "updated_at"])
    token = signing.dumps({"device": str(device.public_id), "version": device.token_version}, salt="pixelcore.device-session", compress=True)
    return device, token


def device_from_token(token, device_types=None, max_age=90 * 24 * 60 * 60):
    try:
        payload = signing.loads(token, salt="pixelcore.device-session", max_age=max_age)
    except signing.BadSignature:
        return None
    queryset = BusinessDevice.objects.select_related("business", "location").filter(
        public_id=payload.get("device"), token_version=payload.get("version"), is_active=True
    )
    if device_types:
        queryset = queryset.filter(device_type__in=device_types)
    return queryset.first()
