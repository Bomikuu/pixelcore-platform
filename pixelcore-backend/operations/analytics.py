"""Bounded analytics summaries over the complete reporting-period queryset."""

from decimal import Decimal

from django.db.models import Count, Sum

from catalog.models import Offering
from commerce.models import Order


def report_analytics(all_orders, order_items):
    product_groups = (
        order_items.values("offering__public_id", "name")
        .annotate(quantity=Sum("quantity"), orders=Count("order_id", distinct=True), sales=Sum("line_total"))
    )
    products = list(product_groups.order_by("-sales", "name", "offering__public_id")[:6])
    item_totals = order_items.aggregate(sales=Sum("line_total"), units=Sum("quantity"))
    offering_ids = [item["offering__public_id"] for item in products if item["offering__public_id"]]
    offerings = {
        item.public_id: item
        for item in Offering.objects.filter(public_id__in=offering_ids)
        .prefetch_related("ordered_media__asset", "assets")
    }
    for item in products:
        public_id = item.pop("offering__public_id")
        item["offering_public_id"] = public_id
        offering = offerings.get(public_id)
        asset = None
        if offering:
            media = next((media for media in offering.ordered_media.all() if media.asset.asset_type == "image"), None)
            asset = media.asset if media else next(
                (asset for asset in offering.assets.all() if asset.asset_type == "image"), None
            )
        item["image_url"] = asset.file.url if asset and asset.file else ""

    categories = list(
        order_items.values("offering__category__name")
        .annotate(sales=Sum("line_total"))
        .order_by("-sales", "offering__category__name")
    )
    category_rows = [
        {"name": row["offering__category__name"] or "Uncategorized", "sales": row["sales"]}
        for row in categories[:5]
    ]
    if len(categories) > 5:
        category_rows.append({"name": "Other categories", "sales": sum(
            (row["sales"] for row in categories[5:]), Decimal("0")
        )})

    status_counts = {row["status"]: row["count"] for row in all_orders.values("status").annotate(count=Count("id"))}
    recent = [
        {
            "public_id": order.public_id,
            "number": order.number,
            "customer_name": " ".join(filter(None, [
                order.customer_snapshot.get("first_name", ""),
                order.customer_snapshot.get("last_name", ""),
            ])).strip() or order.customer_snapshot.get("name") or "Guest customer",
            "grand_total": order.grand_total,
            "status": order.status,
            "placed_at": order.placed_at,
        }
        for order in all_orders.order_by("-placed_at", "-id")[:5]
    ]
    return {
        "top_products": products,
        "categories": category_rows,
        "item_sales": item_totals["sales"] or Decimal("0"),
        "product_summary": {
            "units_sold": item_totals["units"] or 0,
            "products_sold": product_groups.count(),
            "categories_sold": len(categories),
        },
        "status_breakdown": [
            {"key": key, "label": label, "count": status_counts.get(key, 0)}
            for key, label in Order.STATUS_CHOICES
        ],
        "recent_orders": recent,
        "orders_placed": sum(status_counts.values()),
    }
