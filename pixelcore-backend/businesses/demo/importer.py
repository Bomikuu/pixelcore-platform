"""Import a repeatable, isolated sample month without external side effects."""

from django.conf import settings
from django.core.management.base import CommandError
from django.db import transaction

from businesses.models import AuditEvent, Business

from .activity import import_documents, import_orders, import_purchases, reconcile_inventory
from .catalog import import_assets, import_catalog, import_people, prepare_business
from .common import Context, FIXTURE, identity
from .publishing import publish_demo
from .schedule import import_schedule, import_workforce


def import_month(month=None, slug="northline-monthly-demo", owner_email=None, fixture=FIXTURE):
    if not settings.DEBUG:
        raise CommandError("Monthly sample data is restricted to DEBUG development environments.")
    ctx = Context(month, slug, fixture)
    ctx.new_files = []
    try:
        with transaction.atomic():
            prepare_business(ctx, owner_email)
            import_assets(ctx)
            import_catalog(ctx)
            import_people(ctx)
            import_purchases(ctx)
            import_orders(ctx)
            reconcile_inventory(ctx)
            import_documents(ctx)
            import_schedule(ctx)
            import_workforce(ctx)
            publish_demo(ctx)
            audit, _ = AuditEvent.objects.get_or_create(business=ctx.business, action="demo.month_imported",
                resource_type="monthly_fixture", resource_id=ctx.month,
                defaults={"actor": ctx.owner, "metadata": {"orders": len(ctx.data["orders"]), "bookings": len(ctx.data["bookings"]), "fictional": True}})
            ctx.stamp(audit, created_at=min(ctx.now, ctx.first.replace(day=ctx.days)))
    except Exception:
        # Roll back only newly created media, never an existing user's files.
        for storage, name in ctx.new_files:
            storage.delete(name)
        raise
    return ctx


def restore_media(slug="northline-monthly-demo", fixture=FIXTURE):
    """Repair missing demo media in this environment without refreshing activity."""
    if not settings.DEBUG:
        raise CommandError("Monthly sample data is restricted to DEBUG development environments.")
    ctx = Context(None, slug, fixture)
    ctx.new_files = []
    try:
        with transaction.atomic():
            ctx.business = Business.objects.select_for_update().filter(
                slug=slug, public_id=identity(slug, Business, "tenant")
            ).first()
            if ctx.business is None:
                raise CommandError("The managed demo business was not found in this database. Import the sample month first.")
            ctx.owner = ctx.business.created_by
            import_assets(ctx)
    except Exception:
        for storage, name in ctx.new_files:
            storage.delete(name)
        raise
    return ctx
