"""Allowlisted facts only. The model does not calculate or query operational data."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from smokey_assistant.contracts import AssistantError, ResolvedReport

from workforce.models import AttendanceRecord
from operations.models import PaymentAllocation
from commerce.models import OrderItem
from .smokey_bridge import tenant_business


def daily_series(rows, plan, defaults):
    if not rows:
        return []
    by_date = {row["date"]: row for row in rows}
    return [
        by_date.get(day.isoformat(), {"date": day.isoformat(), **defaults})
        for day in (
            plan.date_from + timedelta(days=index)
            for index in range((plan.date_to - plan.date_from).days + 1)
        )
    ]


def resolve_report(context, plan):
    context.require("generate")
    business = tenant_business(context)
    try:
        zone = ZoneInfo(business.timezone)
    except (ValueError, ZoneInfoNotFoundError):
        raise AssistantError(
            "Correct the business timezone before generating reports."
        ) from None
    start = datetime.combine(plan.date_from, time.min, zone)
    end = datetime.combine(plan.date_to + timedelta(days=1), time.min, zone)
    metrics, tables, details, sources, unavailable, charts = {}, {}, [], [], [], {}

    def table(key, label, queryset, row_fn):
        total = queryset.count()
        rows = [row_fn(item) for item in queryset[:10000]]
        tables[key] = {
            "label": label,
            "rows": rows[:100],
            "total": total,
            "stored": len(rows),
            "truncated": total > len(rows),
        }
        details.extend(
            {"table_key": key, "ordinal": index, "data": row}
            for index, row in enumerate(rows)
        )

    if plan.kind in {"daily", "attendance", "late"}:
        if "operate" not in business.enabled_modules:
            unavailable.append("Attendance: Operate is disabled for this business.")
        else:
            records = AttendanceRecord.objects.filter(
                business=business, clock_in__gte=start, clock_in__lt=end
            )
            recorded_late = Q(late_minutes__gt=0) | Q(status="late")
            counts = records.aggregate(
                attended_employees=Count("staff_id", distinct=True),
                late_employees=Count("staff_id", filter=recorded_late, distinct=True),
                excused_late_employees=Count(
                    "staff_id",
                    filter=recorded_late & Q(late_excused=True),
                    distinct=True,
                ),
                unexcused_late_employees=Count(
                    "staff_id",
                    filter=recorded_late & Q(late_excused=False),
                    distinct=True,
                ),
            )
            counts["currently_clocked_in"] = (
                AttendanceRecord.objects.filter(
                    business=business, clock_in__isnull=False, clock_out__isnull=True
                )
                .values("staff_id")
                .distinct()
                .count()
            )
            metrics.update(counts)
            selected = records.filter(recorded_late) if plan.kind == "late" else records
            charts["attendance"] = [
                {"date": row["day"].isoformat(), "records": row["records"]}
                for row in (
                    selected.annotate(day=TruncDate("clock_in", tzinfo=zone))
                    .values("day").annotate(records=Count("pk")).order_by("day")
                )
            ]
            charts["attendance"] = daily_series(charts["attendance"], plan, {"records": 0})
            table(
                "attendance",
                "Late arrivals" if plan.kind == "late" else "Recorded attendance",
                selected.select_related("staff").order_by("clock_in", "pk"),
                lambda record: {
                    "employee": record.staff.display_name,
                    "clock_in": timezone.localtime(record.clock_in, zone).isoformat(),
                    "clock_out": timezone.localtime(record.clock_out, zone).isoformat()
                    if record.clock_out
                    else None,
                    "late_minutes": record.late_minutes,
                    "excused": record.late_excused,
                },
            )
            sources.append(
                {
                    "label": "Workforce attendance",
                    "href": "/workspace/operate/workforce",
                }
            )
    if plan.kind in {"daily", "sales"}:
        if "sell" not in business.enabled_modules:
            unavailable.append("Sales: Sell is disabled for this business.")
        else:
            orders = business.orders.filter(
                placed_at__gte=start, placed_at__lt=end
            ).exclude(status="cancelled")
            metrics.update(
                {
                    "orders": orders.count(),
                    "ordered_sales": format(
                        orders.aggregate(total=Sum("grand_total"))["total"]
                        or Decimal("0.00"),
                        ".2f",
                    ),
                    "paid_orders": orders.filter(payment_status="paid").count(),
                    "currency": business.currency,
                }
            )
            items = OrderItem.objects.filter(order__in=orders)
            metrics["items_sold"] = items.aggregate(total=Sum("quantity"))["total"] or 0
            metrics["average_order_value"] = format(
                Decimal(metrics["ordered_sales"]) / metrics["orders"]
                if metrics["orders"] else Decimal("0.00"),
                ".2f",
            )
            charts["sales"] = [
                {
                    "date": row["day"].isoformat(),
                    "sales": str(row["sales"]),
                    "orders": row["orders"],
                }
                for row in (
                    orders.annotate(day=TruncDate("placed_at", tzinfo=zone))
                    .values("day").annotate(sales=Sum("grand_total"), orders=Count("pk")).order_by("day")
                )
            ]
            charts["sales"] = daily_series(charts["sales"], plan, {"sales": "0.00", "orders": 0})
            charts["payments"] = [
                {
                    "label": row["payment_status"],
                    "orders": row["orders"],
                    "sales": str(row["sales"]),
                }
                for row in (
                    orders.values("payment_status")
                    .annotate(orders=Count("pk"), sales=Sum("grand_total")).order_by("payment_status")
                )
            ]
            if "operate" in business.enabled_modules:
                payments = PaymentAllocation.objects.filter(
                    invoice__business=business,
                    received_at__gte=start,
                    received_at__lt=end,
                )
                metrics["collected_payments"] = format(
                    payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
                    ".2f",
                )
            else:
                unavailable.append(
                    "Collected payments: Operate is disabled for this business."
                )
            table(
                "orders",
                "Orders placed",
                orders.order_by("placed_at", "pk"),
                lambda order: {
                    "order": order.number,
                    "status": order.status,
                    "payment": order.payment_status,
                    "total": str(order.grand_total),
                    "currency": order.currency,
                },
            )

            def transaction_row(item):
                asset = None
                if item.offering_id and item.offering.business_id == business.pk:
                    asset = next(
                        (
                            asset for asset in item.offering.assets.all()
                            if asset.asset_type == "image"
                            and asset.processing_status == "ready"
                            and asset.business_id == business.pk
                        ),
                        None,
                    )
                return {
                    "date": timezone.localtime(item.order.placed_at, zone).isoformat(),
                    "order": item.order.number,
                    "product": item.name,
                    "image_url": asset.file.url if asset and asset.file else None,
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "total": str(item.line_total),
                    "currency": item.order.currency,
                    "payment": item.order.payment_status,
                }

            table(
                "transactions",
                "Product transactions",
                items.select_related("order", "offering")
                .prefetch_related("offering__assets").order_by("order__placed_at", "pk"),
                transaction_row,
            )
            sources.append({"label": "Recorded orders", "href": "/workspace/orders"})
    facts = {
        "version": 1,
        "tenant_id": context.tenant_id,
        "kind": plan.kind,
        **plan.payload(),
        "timezone": business.timezone,
        "generated_at": timezone.now().isoformat(),
        "metrics": metrics,
        "tables": tables,
        "charts": charts,
        "sources": sources,
        "unavailable_sources": unavailable,
    }
    return ResolvedReport(facts, details)
