"""Small, tenant-scoped suggestions for the workspace command search."""

from functools import reduce
from operator import or_
import unicodedata

from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Category, Offering, OfferingMedia
from commerce.models import Discount
from scheduling.models import StaffProfile
from .views import member_business
from .models import BusinessAsset


SEARCH_KINDS = {
    "products": (
        "Products", "sell", Offering,
        ("name", "sku", "variants__sku", "variants__barcode"),
    ),
    "promotions": ("Promotions", "sell", Discount, ("name", "code")),
    "categories": ("Categories", "sell", Category, ("name",)),
    "employees": (
        "Employees", "operate", StaffProfile,
        ("display_name", "employee_code", "job_title"),
    ),
}
KIND_ALIASES = {
    "product": "products",
    "products": "products",
    "item": "products",
    "items": "products",
    "promo": "promotions",
    "promos": "promotions",
    "promotion": "promotions",
    "promotions": "promotions",
    "category": "categories",
    "categories": "categories",
    "employee": "employees",
    "employees": "employees",
    "staff": "employees",
}


def with_search_images(records, kind, business):
    if kind == "categories":
        return records.select_related("cover_asset")
    if kind != "products":
        return records
    images = BusinessAsset.objects.filter(
        business=business, asset_type="image", processing_status="ready"
    )
    return records.prefetch_related(
        Prefetch(
            "ordered_media",
            queryset=OfferingMedia.objects.filter(
                business=business, asset__business=business,
                asset__asset_type="image", asset__processing_status="ready",
            ).select_related("asset"),
            to_attr="search_media",
        ),
        Prefetch("assets", queryset=images, to_attr="search_assets"),
    )


def search_image_url(record, kind, request):
    image = None
    if kind == "employees":
        image = record.profile_image
    elif kind == "categories":
        asset = record.cover_asset
        if (asset and asset.business_id == record.business_id
                and asset.asset_type == "image" and asset.processing_status == "ready"):
            image = asset.file
    elif kind == "products":
        media = sorted(record.search_media, key=lambda item: (
            item.variant_id is not None, item.role != "cover", item.sort_order, item.pk
        ))
        if media:
            image = media[0].asset.file
        if not image:
            image = next((asset.file for asset in record.search_assets if asset.file), None)
    return request.build_absolute_uri(image.url) if image else ""


class WorkspaceSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        query = unicodedata.normalize(
            "NFKC", request.query_params.get("search", "")
        ).strip()
        if len(query) > 120:
            raise ValidationError({"search": "Use 120 characters or fewer."})
        scope = request.query_params.get("scope", "all")
        if scope != "all" and scope not in SEARCH_KINDS:
            raise ValidationError({"scope": "Choose a supported search category."})
        words = query.split()
        kind_hint = KIND_ALIASES.get(words[0].lower()) if words else None
        if kind_hint and scope in ("all", kind_hint):
            scope = kind_hint
            words = words[1:]

        capabilities = list(business.capabilities.values_list("code", "status"))
        # Capability rows are authoritative, including an explicitly disabled set.
        modules = (
            {code for code, status in capabilities if status != "disabled"}
            if capabilities else set(business.enabled_modules)
        )
        role = business.memberships.get(user=request.user, status="active").role
        limit = 5 if query else 3
        now = timezone.now()
        groups = []
        for kind, (label, module, model, fields) in SEARCH_KINDS.items():
            if module not in modules or scope not in ("all", kind):
                continue
            # The destination contains private workforce history and is owner/admin only.
            if kind == "employees" and role not in ("owner", "admin"):
                continue
            records = model.objects.filter(business=business)
            for word in words:
                records = records.filter(reduce(
                    or_, (Q(**{f"{field}__icontains": word}) for field in fields)
                ))
            name_field = "display_name" if kind == "employees" else "name"
            records = records.order_by(name_field, "pk").distinct()
            if not query:
                records = records.order_by("-updated_at", "-pk")
            records = with_search_images(records, kind, business)
            items = []
            for record in records[:limit]:
                if kind == "products":
                    detail = record.sku or record.get_offering_type_display()
                    status = record.status
                elif kind == "promotions":
                    detail = record.code or "Automatic discount"
                    if not record.is_active:
                        status = "inactive"
                    elif record.ends_at and record.ends_at <= now:
                        status = "ended"
                    elif record.starts_at and record.starts_at > now:
                        status = "scheduled"
                    else:
                        status = "active"
                elif kind == "employees":
                    detail = " · ".join(filter(None, [record.employee_code, record.job_title]))
                    status = record.employment_status
                else:
                    detail, status = "Catalog category", "active" if record.is_active else "inactive"
                items.append({
                    "public_id": str(record.public_id),
                    "name": getattr(record, name_field),
                    "detail": detail,
                    "status": status,
                    "image_url": search_image_url(record, kind, request),
                })
            groups.append({"kind": kind, "label": label, "items": items})
        response = Response({"query": query, "groups": groups})
        response["Cache-Control"] = "private, no-store"
        return response
