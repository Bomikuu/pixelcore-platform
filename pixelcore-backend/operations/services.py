import hashlib
import secrets
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from businesses.models import Business
from businesses.services import record_audit
from commerce.models import Fulfillment, Order, OrderItem
from .models import (
    DocumentSequence, InventoryBalance, Invoice, InvoiceLine, PaymentAllocation, PurchaseOrder,
    Quotation, QuotationLine, StockMovement, StockReservation,
)


MONEY = Decimal("0.01")


def signed_token_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@transaction.atomic
def next_document_number(business, document_type, prefix):
    sequence, _ = DocumentSequence.objects.select_for_update().get_or_create(
        business=business,
        document_type=document_type,
        defaults={"prefix": prefix, "next_number": 1},
    )
    value = sequence.next_number
    sequence.next_number = F("next_number") + 1
    sequence.save(update_fields=["next_number"])
    return f"{sequence.prefix}-{timezone.localdate().year}-{value:06d}"


@transaction.atomic
def adjust_stock(balance, quantity_delta, movement_type, actor=None, reference_type="", reference_id="", note=""):
    balance = InventoryBalance.objects.select_for_update().get(pk=balance.pk)
    new_on_hand = balance.on_hand + Decimal(quantity_delta)
    if new_on_hand < balance.reserved:
        raise ValueError("This adjustment would reduce stock below the reserved quantity.")
    balance.on_hand = new_on_hand
    balance.save(update_fields=["on_hand", "updated_at"])
    movement = StockMovement.objects.create(
        business=balance.business,
        balance=balance,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        reference_type=reference_type,
        reference_id=str(reference_id),
        note=note,
        created_by=actor,
    )
    record_audit(balance.business, actor, "inventory.adjusted", "stock_movement", movement.public_id)
    return movement


@transaction.atomic
def transfer_stock(source, destination, quantity, actor=None, note=""):
    quantity = Decimal(quantity)
    if quantity <= 0 or source.variant_id != destination.variant_id or source.business_id != destination.business_id:
        raise ValueError("Transfers require a positive quantity of the same variant within one business.")
    first, second = sorted([source.pk, destination.pk])
    balances = {item.pk: item for item in InventoryBalance.objects.select_for_update().filter(pk__in=(first, second))}
    source, destination = balances[source.pk], balances[destination.pk]
    if source.available < quantity:
        raise ValueError("There is not enough available stock to transfer.")
    reference = secrets.token_hex(8)
    adjust_stock(source, -quantity, "transfer_out", actor, "transfer", reference, note)
    adjust_stock(destination, quantity, "transfer_in", actor, "transfer", reference, note)


@transaction.atomic
def reserve_order_stock(order):
    location = order.cart.location if order.cart_id and order.cart.location_id else order.business.locations.filter(is_primary=True, is_active=True).first()
    for item in order.items.select_related("offering", "variant"):
        if not item.offering.track_inventory:
            continue
        if not item.variant_id or not location:
            raise ValueError(f"Inventory is not configured for {item.name}.")
        balance = InventoryBalance.objects.select_for_update().filter(
            business=order.business,
            variant=item.variant,
            location=location,
        ).first()
        quantity = Decimal(item.quantity)
        if not balance or balance.available < quantity:
            raise ValueError(f"Not enough stock is available for {item.name}.")
        balance.reserved += quantity
        balance.save(update_fields=["reserved", "updated_at"])
        StockReservation.objects.create(
            business=order.business,
            balance=balance,
            order_item=item,
            quantity=quantity,
            expires_at=timezone.now() + timedelta(minutes=30),
        )


@transaction.atomic
def release_expired_reservations():
    reservations = StockReservation.objects.select_for_update().filter(status="active", expires_at__lte=timezone.now())
    count = 0
    for reservation in reservations:
        balance = InventoryBalance.objects.select_for_update().get(pk=reservation.balance_id)
        balance.reserved = max(Decimal("0"), balance.reserved - reservation.quantity)
        balance.save(update_fields=["reserved", "updated_at"])
        reservation.status = "expired"
        reservation.save(update_fields=["status"])
        count += 1
    return count


@transaction.atomic
def commit_order_stock(order, actor=None):
    for reservation in StockReservation.objects.select_for_update().filter(order_item__order=order, status="active"):
        balance = InventoryBalance.objects.select_for_update().get(pk=reservation.balance_id)
        if balance.on_hand < reservation.quantity or balance.reserved < reservation.quantity:
            raise ValueError("Reserved stock is no longer consistent with the inventory balance.")
        balance.on_hand -= reservation.quantity
        balance.reserved -= reservation.quantity
        balance.save(update_fields=["on_hand", "reserved", "updated_at"])
        StockMovement.objects.create(
            business=order.business,
            balance=balance,
            movement_type="sale",
            quantity_delta=-reservation.quantity,
            reference_type="order",
            reference_id=str(order.public_id),
            created_by=actor,
        )
        reservation.status = "committed"
        reservation.save(update_fields=["status"])


@transaction.atomic
def release_order_stock(order):
    for reservation in StockReservation.objects.select_for_update().filter(order_item__order=order, status="active"):
        balance = InventoryBalance.objects.select_for_update().get(pk=reservation.balance_id)
        balance.reserved = max(Decimal("0"), balance.reserved - reservation.quantity)
        balance.save(update_fields=["reserved", "updated_at"])
        reservation.status = "released"
        reservation.save(update_fields=["status"])


@transaction.atomic
def receive_purchase_order(purchase_order, receipts, actor=None):
    purchase_order = PurchaseOrder.objects.select_for_update().get(pk=purchase_order.pk)
    if purchase_order.status in {"received", "cancelled"}:
        raise ValueError(f"A {purchase_order.status.replace('_', ' ')} purchase order cannot receive more stock.")
    received_any = False
    for line in purchase_order.lines.select_related("variant"):
        quantity = Decimal(str(receipts.get(str(line.public_id), 0)))
        if quantity < 0 or line.quantity_received + quantity > line.quantity_ordered:
            raise ValueError(f"Invalid received quantity for {line.description}.")
        if quantity:
            received_any = True
            balance, _ = InventoryBalance.objects.get_or_create(
                business=purchase_order.business,
                variant=line.variant,
                location=purchase_order.location,
            )
            adjust_stock(balance, quantity, "receive", actor, "purchase_order", purchase_order.public_id)
            line.quantity_received += quantity
            line.save(update_fields=["quantity_received"])
    if not received_any:
        raise ValueError("Enter at least one received quantity.")
    totals = list(purchase_order.lines.values_list("quantity_ordered", "quantity_received"))
    fully_received = bool(totals) and all(received >= ordered for ordered, received in totals)
    purchase_order.status = "received" if fully_received else "partially_received"
    if fully_received and not purchase_order.received_at:
        purchase_order.received_at = timezone.now()
    purchase_order.save(update_fields=["status", "received_at", "updated_at"])
    return purchase_order


def calculate_lines(lines, prices_include_tax=True):
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    normalized = []
    for line in lines:
        quantity = Decimal(str(line["quantity"]))
        price = Decimal(str(line["unit_price"]))
        rate = Decimal(str(line.get("tax_rate", 0)))
        total = (quantity * price).quantize(MONEY, rounding=ROUND_HALF_UP)
        subtotal += total
        ratio = rate / Decimal("100")
        tax_total += total - total / (1 + ratio) if prices_include_tax and ratio else total * ratio
        normalized.append({**line, "quantity": quantity, "unit_price": price, "tax_rate": rate, "line_total": total})
    tax_total = tax_total.quantize(MONEY, rounding=ROUND_HALF_UP)
    grand_total = subtotal if prices_include_tax else subtotal + tax_total
    return normalized, subtotal, tax_total, grand_total


@transaction.atomic
def create_quotation(business, customer, lines, data, actor=None):
    normalized, subtotal, tax_total, grand_total = calculate_lines(lines, business.prices_include_tax)
    raw_token = secrets.token_urlsafe(32)
    quotation = Quotation.objects.create(
        business=business,
        customer=customer,
        number=next_document_number(business, "quotation", "QUO"),
        currency=business.currency,
        subtotal=subtotal,
        tax_total=tax_total,
        grand_total=grand_total,
        acceptance_token_digest=signed_token_digest(raw_token),
        expires_at=data.get("expires_at"),
        notes=data.get("notes", ""),
        status=data.get("status", "draft"),
    )
    for line in normalized:
        QuotationLine.objects.create(quotation=quotation, **line)
    record_audit(business, actor, "quotation.created", "quotation", quotation.public_id)
    return quotation, raw_token


@transaction.atomic
def create_invoice(business, customer, lines, data, actor=None):
    normalized, subtotal, tax_total, grand_total = calculate_lines(lines, business.prices_include_tax)
    invoice = Invoice.objects.create(
        business=business,
        customer=customer,
        order=data.get("order"),
        number=next_document_number(business, "invoice", "INV"),
        currency=business.currency,
        status=data.get("status", "draft"),
        issued_at=data.get("issued_at"),
        due_at=data.get("due_at"),
        subtotal=subtotal,
        tax_total=tax_total,
        grand_total=grand_total,
        notes=data.get("notes", ""),
    )
    for line in normalized:
        InvoiceLine.objects.create(invoice=invoice, **line)
    if not business.currency_locked_at:
        business.currency_locked_at = timezone.now()
        business.save(update_fields=["currency_locked_at", "updated_at"])
    record_audit(business, actor, "invoice.created", "invoice", invoice.public_id)
    return invoice


@transaction.atomic
def create_order_from_quotation(quotation, actor=None):
    business = Business.objects.select_for_update().get(pk=quotation.business_id)
    order = Order.objects.create(
        business=business,
        customer=quotation.customer,
        number=f"ORD-{timezone.localdate().year}-{business.orders.count() + 1:06d}",
        status="confirmed",
        payment_status="unpaid",
        payment_method="manual",
        fulfillment_type="none",
        currency=quotation.currency,
        subtotal=quotation.subtotal,
        tax_total=quotation.tax_total,
        shipping_total=0,
        discount_total=0,
        grand_total=quotation.grand_total,
        customer_snapshot={
            "email": quotation.customer.email,
            "first_name": quotation.customer.first_name,
            "last_name": quotation.customer.last_name,
            "phone": quotation.customer.phone,
        },
        notes=f"Converted from quotation {quotation.number}",
    )
    for line in quotation.lines.all():
        integral_quantity = line.quantity.to_integral_value()
        if line.quantity != integral_quantity:
            raise ValueError("Order conversion requires whole-number quotation quantities.")
        OrderItem.objects.create(
            order=order,
            name=line.description,
            quantity=int(integral_quantity),
            unit_price=line.unit_price,
            tax_rate=line.tax_rate,
            line_total=line.line_total,
            offering_snapshot={"type": "quotation_line", "source_quotation": str(quotation.public_id)},
        )
    Fulfillment.objects.create(order=order, fulfillment_type="none")
    if not business.currency_locked_at:
        business.currency_locked_at = timezone.now()
        business.save(update_fields=["currency_locked_at", "updated_at"])
    record_audit(business, actor, "quotation.converted_to_order", "order", order.public_id, {"quotation": str(quotation.public_id)})
    return order


@transaction.atomic
def allocate_invoice_payment(invoice, amount, actor, reference="", payment_attempt=None):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    amount = Decimal(amount).quantize(MONEY)
    if amount <= 0 or invoice.amount_paid + amount > invoice.grand_total:
        raise ValueError("Payment allocation must be positive and cannot exceed the invoice balance.")
    PaymentAllocation.objects.create(invoice=invoice, amount=amount, reference=reference, payment_attempt=payment_attempt, received_at=timezone.now(), created_by=actor)
    invoice.amount_paid += amount
    invoice.status = "paid" if invoice.amount_paid == invoice.grand_total else "partially_paid"
    invoice.save(update_fields=["amount_paid", "status", "updated_at"])
    return invoice
