import hashlib
import json

from django.core import signing
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from businesses.services import record_audit
from .blocks import validate_page_content
from .models import PageRevision


@transaction.atomic
def create_revision(page, content, actor):
    validate_page_content(content, page.site.business)
    page = page.__class__.objects.select_for_update().get(pk=page.pk)
    number = (page.revisions.aggregate(maximum=Max("number"))["maximum"] or 0) + 1
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    revision = PageRevision.objects.create(
        page=page,
        number=number,
        schema_version=content["schema_version"],
        content=content,
        checksum=hashlib.sha256(canonical.encode()).hexdigest(),
        created_by=actor,
    )
    page.draft_revision = revision
    page.status = "published" if page.published_revision_id else "draft"
    page.save(update_fields=["draft_revision", "status", "updated_at"])
    record_audit(page.site.business, actor, "site.revision_created", "page_revision", revision.public_id, {"page": str(page.public_id)})
    return revision


@transaction.atomic
def publish_revision(page, revision, actor):
    validate_page_content(revision.content, page.site.business)
    if revision.page_id != page.id:
        raise ValueError("Revision does not belong to this page.")
    page = page.__class__.objects.select_for_update().get(pk=page.pk)
    page.published_revision = revision
    page.draft_revision = revision
    page.status = "published"
    page.published_at = timezone.now()
    page.save(update_fields=["published_revision", "draft_revision", "status", "published_at", "updated_at"])
    page.site.status = "published"
    page.site.published_at = timezone.now()
    page.site.cache_version += 1
    page.site.save(update_fields=["status", "published_at", "cache_version", "updated_at"])
    record_audit(page.site.business, actor, "site.page_published", "site_page", page.public_id, {"revision": revision.number})
    return page


def make_preview_token(page, revision):
    return signing.dumps({"page": str(page.public_id), "revision": str(revision.public_id)}, salt="pixelcore-page-preview", compress=True)


def read_preview_token(token, max_age=3600):
    return signing.loads(token, salt="pixelcore-page-preview", max_age=max_age)
