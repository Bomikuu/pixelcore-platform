"""PixelCore-owned identity boundary for the optional Smokey runtime."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from .models import Business, BusinessMembership
from .views import member_business


def smokey_available():
    return "smokey_assistant" in settings.INSTALLED_APPS


def context_for(user, business_id, action):
    from smokey_assistant.contracts import HostContext

    if not smokey_available():
        raise PermissionDenied("Smokey is not installed on this server.")
    business = member_business(user, business_id, roles=("owner", "admin", "manager"))
    if (
        business.status != "active"
        or not business.capabilities.filter(code="smokey", status="active").exists()
    ):
        raise PermissionDenied("Enable Smokey for this business first.")
    role = BusinessMembership.objects.get(
        business=business, user=user, status="active"
    ).role
    actions = {"generate", "view_reports"}
    if role in {"owner", "admin"}:
        actions |= {"configure", "delete_reports"}
    context = HostContext(
        f"pixelcore:{business.public_id}",
        str(user.pk),
        business.timezone,
        frozenset(actions),
    )
    context.require(action)
    return context


def assistant_context(request, business_public_id, action):
    return context_for(request.user, business_public_id, action)


def worker_context(tenant_id, actor_id, action):
    if not tenant_id.startswith("pixelcore:"):
        raise PermissionDenied("Unknown assistant tenant.")
    user = get_user_model().objects.get(pk=actor_id, is_active=True)
    return context_for(user, tenant_id.split(":", 1)[1], action)


def tenant_business(context):
    return Business.objects.get(public_id=context.tenant_id.split(":", 1)[1])
