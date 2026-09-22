from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from catalog.models import Offering


def discount_states(now=None):
    now = now or timezone.now()
    valid_end = Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    return {
        "active": Q(is_active=True) & (Q(starts_at__isnull=True) | Q(starts_at__lte=now)) & valid_end,
        "scheduled": Q(is_active=True, starts_at__gt=now) & valid_end,
        "ended": Q(is_active=True, ends_at__lte=now),
        "inactive": Q(is_active=False),
    }


def eligible_offering_ids(discount):
    if not discount.offering_ids and not discount.category_ids:
        return None
    offerings = Offering.objects.filter(business=discount.business)
    if discount.category_ids:
        offerings = offerings.filter(category__public_id__in=discount.category_ids)
    else:
        offerings = offerings.filter(public_id__in=discount.offering_ids)
    return set(str(value) for value in offerings.values_list("public_id", flat=True))


def discount_amount(discount, lines):
    """Price eligible lines identically in the storefront cart and POS preview."""
    if not discount:
        return Decimal("0")
    now = timezone.now()
    if not discount.is_active or (discount.starts_at and discount.starts_at > now) or (discount.ends_at and discount.ends_at <= now):
        return Decimal("0")
    allowed = eligible_offering_ids(discount)
    eligible = sum((Decimal(total) for offering_id, total in lines if allowed is None or str(offering_id) in allowed), Decimal("0"))
    amount = eligible * discount.value / Decimal("100") if discount.value_type == "percentage" else discount.value
    return min(eligible, amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
