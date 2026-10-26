"""Connected sales, purchasing, invoice and stock history for a sample month."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum

from commerce.models import Fulfillment, Order, OrderItem, PaymentAttempt, Refund
from operations.models import (
    Expense, ExpenseCategory, Invoice, InvoiceLine, PaymentAllocation, PurchaseOrder,
    PurchaseOrderLine, Quotation, QuotationLine, StockMovement, StockReservation,
)

from .common import TAX, identity, money


def movement(ctx, key, balance, quantity, kind, reference, at):
    obj = ctx.save(StockMovement, key, business=ctx.business, balance=balance,
        quantity_delta=quantity, movement_type=kind, reference_type="monthly_demo",
        reference_id=str(reference), note="Fictional monthly demo ledger entry.", created_by=ctx.owner)
    return ctx.stamp(obj, created_at=at)


def import_purchases(ctx):
    for index, row in enumerate(ctx.data["purchase_orders"]):
        at = ctx.at(row["day"], history=True)
        po = ctx.save(PurchaseOrder, ctx.monthly(row["id"]), business=ctx.business,
            supplier=ctx.suppliers[row["supplier"]], location=ctx.location,
            number=f"DEMO-{ctx.month.replace('-', '')}-PO{index + 1:03}", status=row["status"],
            ordered_at=at.date(), expected_at=(at + timedelta(days=4)).date(),
            received_at=at if row["status"] in {"received", "partially_received"} else None,
            notes="Fictional replenishment order; no supplier was contacted.")
        ctx.stamp(po, created_at=at, updated_at=at)
        for n, item in enumerate(row["items"]):
            received = item["quantity"] if row["status"] == "received" else item["quantity"] // 2 if row["status"] == "partially_received" else 0
            ctx.save(PurchaseOrderLine, ctx.monthly(f"{row['id']}:line:{n}"), purchase_order=po,
                variant=ctx.variants[item["variant"]], description=ctx.variants[item["variant"]].offering.name,
                quantity_ordered=item["quantity"], quantity_received=received, unit_cost=ctx.costs[item["variant"]])
            if received:
                movement(ctx, ctx.monthly(f"{row['id']}:receipt:{n}"), ctx.balances[item["variant"]],
                         received, "receive", po.public_id, at)


def import_orders(ctx):
    for index, row in enumerate(ctx.data["orders"]):
        at = ctx.at(row["day"], row["hour"], row["minute"], history=True)
        customer = ctx.customers[row["customer"]]
        address = customer.addresses.get(is_default=True)
        subtotal = sum((ctx.variants[item["variant"]].price * item["quantity"] for item in row["items"]), Decimal("0"))
        tax = money(subtotal * TAX)
        shipping = money("120" if row["fulfillment"] == "delivery" else "0")
        payment_status = "paid" if row["status"] in {"fulfilled", "processing"} else "refunded" if row["status"] == "refunded" else "pending" if row["status"] == "confirmed" else "unpaid"
        order = ctx.save(Order, ctx.monthly(row["id"]), business=ctx.business, customer=customer,
            number=f"DEMO-{ctx.month.replace('-', '')}-S{index + 1:03}", status=row["status"],
            payment_status=payment_status, payment_method=row["payment_method"], fulfillment_type=row["fulfillment"],
            currency=ctx.business.currency, subtotal=subtotal, tax_total=tax, shipping_total=shipping,
            discount_total=0, grand_total=subtotal + tax + shipping,
            customer_snapshot={"first_name": customer.first_name, "last_name": customer.last_name, "email": customer.email, "phone": customer.phone},
            shipping_snapshot={"recipient_name": address.recipient_name, "line1": address.line1,
                               "city": address.city, "region": address.region, "postal_code": address.postal_code, "country": address.country},
            notes="Fictional demonstration sale. No real payment was processed.")
        ctx.stamp(order, placed_at=at, updated_at=at)
        for n, item in enumerate(row["items"]):
            variant = ctx.variants[item["variant"]]
            line = ctx.save(OrderItem, ctx.monthly(f"{row['id']}:line:{n}"), order=order,
                offering=variant.offering, variant=variant, name=variant.offering.name, sku=variant.sku,
                quantity=item["quantity"], unit_price=variant.price, tax_rate=Decimal("12.000"),
                line_total=variant.price * item["quantity"],
                offering_snapshot={"offering_type": "physical", "name": variant.offering.name, "variant": variant.name})
            balance = ctx.balances[item["variant"]]
            committed = row["status"] in {"fulfilled", "refunded"}
            reservation_status = "committed" if committed else "released" if row["status"] == "cancelled" else "expired" if at + timedelta(hours=24) < ctx.now else "active"
            reservation = ctx.save(StockReservation, ctx.monthly(f"{row['id']}:reservation:{n}"),
                business=ctx.business, balance=balance, order_item=line, quantity=item["quantity"],
                status=reservation_status, expires_at=at + timedelta(hours=24))
            ctx.stamp(reservation, created_at=at)
            if committed:
                movement(ctx, ctx.monthly(f"{row['id']}:sale:{n}"), balance, -item["quantity"], "sale", order.public_id, at)
                if row["status"] == "refunded":
                    movement(ctx, ctx.monthly(f"{row['id']}:return:{n}"), balance, item["quantity"], "return", order.public_id, at)
        fulfillment_status = "fulfilled" if row["status"] in {"fulfilled", "refunded"} else "cancelled" if row["status"] == "cancelled" else "ready" if row["status"] == "processing" else "pending"
        ctx.save(Fulfillment, ctx.monthly(f"{row['id']}:fulfillment"), order=order,
            fulfillment_type=row["fulfillment"], status=fulfillment_status,
            tracking_reference=f"DEMO-{ctx.month.replace('-', '')}-{index + 1:04}" if row["fulfillment"] == "delivery" else "",
            fulfilled_at=at if fulfillment_status == "fulfilled" else None, metadata={"demo": True})
        if payment_status in {"paid", "pending", "refunded"}:
            payment = ctx.save(PaymentAttempt, ctx.monthly(f"{row['id']}:payment"), business=ctx.business,
                order=order, provider="manual", provider_reference=f"DEMO-PAY-{ctx.month}-{index + 1:03}",
                status="pending" if payment_status == "pending" else "paid", amount=order.grand_total,
                currency=ctx.business.currency, idempotency_key=f"{ctx.business.public_id}:{ctx.month}:{row['id']}", raw_status={"demo": True})
            ctx.stamp(payment, created_at=at, updated_at=at)
            if row["status"] == "refunded":
                refund = ctx.save(Refund, ctx.monthly(f"{row['id']}:refund"), payment_attempt=payment,
                    amount=order.grand_total, reason="Fictional customer return", status="completed", created_by=ctx.owner)
                ctx.stamp(refund, created_at=at)


def reconcile_inventory(ctx):
    statistics = {}
    for key, balance in ctx.balances.items():
        opening_id = identity(ctx.slug, StockMovement, f"opening:{key}")
        other = balance.movements.exclude(public_id=opening_id)
        net = other.aggregate(total=Sum("quantity_delta"))["total"] or Decimal("0")
        reserved = balance.reservations.filter(status="active").aggregate(total=Sum("quantity"))["total"] or Decimal("0")
        earliest = other.order_by("created_at").values_list("created_at", flat=True).first() or ctx.first
        statistics[key] = (net, reserved, earliest)
    low_key = min(statistics, key=lambda key: statistics[key][0] - statistics[key][1])
    for key, balance in ctx.balances.items():
        net, reserved, earliest = statistics[key]
        # A low-stock example still has enough physical units for its reservations.
        opening = max(Decimal("0"), reserved + 3 - net) if key == low_key else max(Decimal("60"), reserved + 12 - net)
        movement(ctx, f"opening:{key}", balance, opening, "adjust", "opening-balance", min(ctx.first, earliest))
        balance.on_hand, balance.reserved = opening + net, reserved
        balance.last_counted_at = min(ctx.now.date(), ctx.first.replace(day=ctx.days).date())
        balance.save(update_fields=["on_hand", "reserved", "last_counted_at", "updated_at"])


def import_documents(ctx):
    for index, row in enumerate(ctx.data["invoices"]):
        at = ctx.at(row["day"], history=True)
        service = ctx.services[row["service"]]
        subtotal = service.base_price * row["quantity"]
        tax = money(subtotal * TAX)
        total = subtotal + tax
        paid = total if row["status"] == "paid" else money(total / 2) if row["status"] == "partially_paid" else money(0)
        due = (at + timedelta(days=15)).date()
        status = row["status"]
        if status == "overdue":
            # Overdue is only meaningful after the actual due date.
            due = at.date()
            if due >= ctx.now.date():
                status = "issued"
        invoice = ctx.save(Invoice, ctx.monthly(row["id"]), business=ctx.business,
            customer=ctx.customers[row["customer"]], number=f"DEMO-{ctx.month.replace('-', '')}-INV{index + 1:03}",
            status=status, currency=ctx.business.currency, issued_at=at.date(), due_at=due,
            subtotal=subtotal, tax_total=tax, grand_total=total, amount_paid=paid,
            notes="Fictional workshop/service invoice, separate from retail order payments.")
        ctx.stamp(invoice, created_at=at, updated_at=at)
        ctx.invoices[row["id"]] = invoice
        ctx.save(InvoiceLine, ctx.monthly(f"{row['id']}:line"), invoice=invoice, description=service.name,
            quantity=row["quantity"], unit_price=service.base_price, tax_rate=12, line_total=subtotal)
        if paid:
            allocation = ctx.save(PaymentAllocation, ctx.monthly(f"{row['id']}:payment"), invoice=invoice,
                amount=paid, reference=f"DEMO-SERVICE-{ctx.month}-{index + 1:03}", received_at=at, created_by=ctx.owner)
            ctx.stamp(allocation, created_at=at)
    for index, row in enumerate(ctx.data["quotations"]):
        at = ctx.at(row["day"], history=True)
        service = ctx.services[row["service"]]
        subtotal = service.base_price * row["quantity"]
        tax = money(subtotal * TAX)
        expires = at + timedelta(days=14)
        status = row["status"]
        if status == "expired":
            expires = at
            if expires >= ctx.now:
                status = "sent"
        quote = ctx.save(Quotation, ctx.monthly(row["id"]), business=ctx.business,
            customer=ctx.customers[row["customer"]], number=f"DEMO-{ctx.month.replace('-', '')}-Q{index + 1:03}",
            status=status, currency=ctx.business.currency, subtotal=subtotal, tax_total=tax,
            grand_total=subtotal + tax, acceptance_token_digest="", expires_at=expires,
            accepted_at=at if status in {"accepted", "converted"} else None,
            converted_invoice=ctx.invoices.get(row["invoice"]), notes="Fictional service quotation; no acceptance link was sent.")
        ctx.stamp(quote, created_at=at, updated_at=at)
        ctx.save(QuotationLine, ctx.monthly(f"{row['id']}:line"), quotation=quote, description=service.name,
            quantity=row["quantity"], unit_price=service.base_price, tax_rate=12, line_total=subtotal)
    categories = {}
    for index, row in enumerate(ctx.data["expenses"]):
        at = ctx.at(row["day"], history=True)
        name = row["category"]
        if name not in categories:
            categories[name] = ctx.save(ExpenseCategory, f"expense-category:{name}", business=ctx.business, name=name)
        expense = ctx.save(Expense, ctx.monthly(row["id"]), business=ctx.business, category=categories[name],
            description=row["description"], amount=money(row["amount"]), tax_amount=0,
            incurred_at=at.date(), payment_method=row["payment_method"],
            reference=f"DEMO-{ctx.month.replace('-', '')}-EXP{index + 1:03}", created_by=ctx.owner)
        ctx.stamp(expense, created_at=at, updated_at=at)
