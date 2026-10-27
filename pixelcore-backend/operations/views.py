import secrets
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db.models import Count, F, Q, Sum
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.api import BusinessScopedModelViewSet, BusinessScopedReadOnlyViewSet
from businesses.models import Business
from businesses.views import member_business
from commerce.models import OrderItem
from .analytics import report_analytics
from .models import (
    Expense, ExpenseCategory, InventoryBalance, Invoice, PaymentAllocation, PurchaseOrder, Quotation,
    StockMovement, Supplier, SupplierProduct,
)
from .serializers import (
    ExpenseCategorySerializer, ExpenseSerializer, InventoryBalanceSerializer, InvoiceSerializer,
    PurchaseOrderSerializer, QuotationSerializer, StockMovementSerializer, SupplierProductSerializer, SupplierSerializer,
)
from .services import adjust_stock, allocate_invoice_payment, create_invoice, create_order_from_quotation, receive_purchase_order, signed_token_digest, transfer_stock


class InventoryBalanceViewSet(BusinessScopedModelViewSet):
    queryset = InventoryBalance.objects.select_related(
        "variant__offering",
        "location",
        "preferred_supplier__image",
    ).prefetch_related(
        "variant__ordered_media__asset",
        "variant__offering__ordered_media__asset",
    )
    serializer_class = InventoryBalanceSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    audit_resource = "inventory_balance"

    def get_queryset(self):
        queryset = super().get_queryset()
        supplier_public_id = self.request.query_params.get("supplier")
        return queryset.filter(preferred_supplier__public_id=supplier_public_id) if supplier_public_id else queryset


class StockMovementViewSet(BusinessScopedReadOnlyViewSet):
    queryset = StockMovement.objects.select_related("balance")
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        balance_public_id = self.request.query_params.get("balance_public_id")
        return queryset.filter(balance__public_id=balance_public_id) if balance_public_id else queryset


class SupplierViewSet(BusinessScopedModelViewSet):
    queryset = Supplier.objects.select_related("image").prefetch_related(
        "supplied_products__variant__ordered_media__asset",
        "supplied_products__variant__offering__ordered_media__asset",
    ).annotate(
        purchase_order_count=Count("purchase_orders", distinct=True),
        open_purchase_order_count=Count(
            "purchase_orders",
            filter=Q(purchase_orders__status__in=("ordered", "partially_received")),
            distinct=True,
        ),
        expense_count=Count("expenses", distinct=True),
        preferred_inventory_count=Count("preferred_inventory_balances", distinct=True),
        product_count=Count("supplied_products", distinct=True),
    )
    serializer_class = SupplierSerializer
    audit_resource = "supplier"


class SupplierProductViewSet(BusinessScopedModelViewSet):
    queryset = SupplierProduct.objects.select_related("supplier", "variant__offering")
    serializer_class = SupplierProductSerializer
    audit_resource = "supplier_product"

    def get_queryset(self):
        queryset = super().get_queryset()
        supplier_public_id = self.request.query_params.get("supplier")
        return queryset.filter(supplier__public_id=supplier_public_id) if supplier_public_id else queryset


class PurchaseOrderViewSet(BusinessScopedModelViewSet):
    queryset = PurchaseOrder.objects.select_related("supplier__image", "location").prefetch_related(
        "lines__variant__ordered_media__asset",
        "lines__variant__offering__ordered_media__asset",
    )
    serializer_class = PurchaseOrderSerializer
    audit_resource = "purchase_order"

    def get_queryset(self):
        queryset = super().get_queryset()
        supplier_public_id = self.request.query_params.get("supplier")
        return queryset.filter(supplier__public_id=supplier_public_id) if supplier_public_id else queryset


class QuotationViewSet(BusinessScopedModelViewSet):
    queryset = Quotation.objects.select_related("customer").prefetch_related("lines")
    serializer_class = QuotationSerializer
    audit_resource = "quotation"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save(business=self.get_business())
        payload = QuotationSerializer(quotation, context=self.get_serializer_context()).data
        payload["acceptance_token"] = quotation.acceptance_token
        return Response(payload, status=status.HTTP_201_CREATED)


class InvoiceViewSet(BusinessScopedModelViewSet):
    queryset = Invoice.objects.select_related("customer", "order").prefetch_related("lines", "payment_allocations")
    serializer_class = InvoiceSerializer
    audit_resource = "invoice"


class ExpenseCategoryViewSet(BusinessScopedModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    audit_resource = "expense_category"


class ExpenseViewSet(BusinessScopedModelViewSet):
    queryset = Expense.objects.select_related("category", "supplier__image", "receipt")
    serializer_class = ExpenseSerializer
    audit_resource = "expense"

    def get_queryset(self):
        queryset = super().get_queryset()
        supplier_public_id = self.request.query_params.get("supplier")
        return queryset.filter(supplier__public_id=supplier_public_id) if supplier_public_id else queryset


class InventoryAdjustView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, balance_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        balance = get_object_or_404(InventoryBalance, business=business, public_id=balance_id)
        try:
            quantity = Decimal(str(request.data.get("quantity_delta")))
            movement = adjust_stock(balance, quantity, "adjust", request.user, note=str(request.data.get("note", ""))[:300])
        except (ValueError, TypeError, ArithmeticError) as exc:
            return Response({"error": {"code": "INVENTORY_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        return Response(StockMovementSerializer(movement).data, status=201)


class InventoryTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        source = get_object_or_404(InventoryBalance, business=business, public_id=request.data.get("source_balance_public_id"))
        destination = get_object_or_404(InventoryBalance, business=business, public_id=request.data.get("destination_balance_public_id"))
        try:
            transfer_stock(source, destination, request.data.get("quantity"), request.user, str(request.data.get("note", ""))[:300])
        except (ValueError, TypeError, ArithmeticError) as exc:
            return Response({"error": {"code": "INVENTORY_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PurchaseOrderReceiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, purchase_order_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        purchase_order = get_object_or_404(PurchaseOrder, business=business, public_id=purchase_order_id)
        try:
            receive_purchase_order(purchase_order, request.data.get("receipts", {}), request.user)
        except ValueError as exc:
            return Response({"error": {"code": "RECEIVING_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        purchase_order.refresh_from_db()
        return Response(PurchaseOrderSerializer(purchase_order, context={"business": business, "request": request}).data)


class PublicQuotationAcceptanceView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_quotation(self, slug, quotation_id, token, lock=False):
        queryset = Quotation.objects.select_related("business", "customer").prefetch_related("lines")
        if lock:
            queryset = queryset.select_for_update()
        quotation = get_object_or_404(queryset, business__slug=slug, public_id=quotation_id)
        if not secrets.compare_digest(quotation.acceptance_token_digest, signed_token_digest(token)):
            return None
        return quotation

    def get(self, request, slug, quotation_id):
        quotation = self.get_quotation(slug, quotation_id, request.query_params.get("token", ""))
        if not quotation:
            return Response({"error": {"code": "NOT_FOUND", "message": "Quotation not found.", "details": {}}}, status=404)
        return Response(QuotationSerializer(quotation, context={"business": quotation.business, "request": request}).data)

    @transaction.atomic
    def post(self, request, slug, quotation_id):
        quotation = self.get_quotation(slug, quotation_id, request.data.get("token", ""), lock=True)
        if not quotation:
            return Response({"error": {"code": "NOT_FOUND", "message": "Quotation not found.", "details": {}}}, status=404)
        if quotation.expires_at and quotation.expires_at <= timezone.now():
            quotation.status = "expired"
            quotation.save(update_fields=["status"])
            return Response({"error": {"code": "QUOTATION_EXPIRED", "message": "This quotation has expired.", "details": {}}}, status=410)
        if quotation.status not in {"sent", "draft"}:
            return Response({"error": {"code": "QUOTATION_CONFLICT", "message": "This quotation has already been resolved.", "details": {}}}, status=409)
        convert_to = request.data.get("convert_to")
        if convert_to not in (None, "", "order", "invoice"):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose order or invoice conversion.", "details": {}}}, status=400)
        if convert_to == "order" and any(line.quantity != line.quantity.to_integral_value() for line in quotation.lines.all()):
            return Response({"error": {"code": "QUOTATION_CONVERSION_CONFLICT", "message": "Order conversion requires whole-number quotation quantities.", "details": {}}}, status=409)
        quotation.status = "accepted"
        quotation.accepted_at = timezone.now()
        quotation.save(update_fields=["status", "accepted_at", "updated_at"])
        if convert_to == "invoice":
            lines = [{"description": line.description, "quantity": line.quantity, "unit_price": line.unit_price, "tax_rate": line.tax_rate} for line in quotation.lines.all()]
            invoice = create_invoice(quotation.business, quotation.customer, lines, {"status": "issued", "issued_at": timezone.localdate()})
            quotation.converted_invoice = invoice
            quotation.status = "converted"
            quotation.save(update_fields=["converted_invoice", "status", "updated_at"])
        elif convert_to == "order":
            order = create_order_from_quotation(quotation)
            quotation.converted_order = order
            quotation.status = "converted"
            quotation.save(update_fields=["converted_order", "status", "updated_at"])
        return Response(QuotationSerializer(quotation, context={"business": quotation.business, "request": request}).data)


class InvoicePaymentAllocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, invoice_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        invoice = get_object_or_404(Invoice, business=business, public_id=invoice_id)
        try:
            invoice = allocate_invoice_payment(invoice, request.data.get("amount"), request.user, str(request.data.get("reference", ""))[:120])
        except (ValueError, TypeError, ArithmeticError) as exc:
            return Response({"error": {"code": "PAYMENT_ALLOCATION_CONFLICT", "message": str(exc), "details": {}}}, status=409)
        return Response(InvoiceSerializer(invoice, context={"business": business, "request": request}).data)


class InvoicePdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id, invoice_id):
        business = member_business(request.user, public_id)
        invoice = get_object_or_404(Invoice.objects.select_related("customer").prefetch_related("lines"), business=business, public_id=invoice_id)
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        pdf.setTitle(f"{invoice.number} - {business.display_name}")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(48, height - 54, business.display_name[:80])
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawRightString(width - 48, height - 54, f"Invoice {invoice.number}")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(48, height - 74, f"TIN: {business.tax_id or 'Not provided'} | VAT status: {business.get_tax_status_display()}")
        pdf.drawString(48, height - 96, f"Customer: {invoice.customer.first_name} {invoice.customer.last_name} ({invoice.customer.email})"[:110])
        y = height - 132
        for line in invoice.lines.all():
            pdf.drawString(48, y, line.description[:72])
            pdf.drawRightString(width - 48, y, f"{line.quantity} x {line.unit_price} = {line.line_total} {invoice.currency}")
            y -= 18
            if y < 90:
                pdf.showPage()
                y = height - 54
        y -= 8
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawRightString(width - 48, y, f"Total: {invoice.grand_total} {invoice.currency}")
        pdf.setFont("Helvetica", 8)
        pdf.drawString(48, 48, "Operational commercial record only. Not represented as a BIR-authorized invoice or receipt.")
        pdf.save()
        output.seek(0)
        return FileResponse(output, as_attachment=False, filename=f"{invoice.number}.pdf", content_type="application/pdf")


class BusinessReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        try:
            business_timezone = ZoneInfo(business.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            business_timezone = timezone.get_default_timezone()
        with timezone.override(business_timezone):
            return self.build_report(request, business)

    def build_report(self, request, business):
        try:
            date_from = date.fromisoformat(request.query_params.get("date_from", str(timezone.localdate().replace(day=1))))
            date_to = date.fromisoformat(request.query_params.get("date_to", str(timezone.localdate())))
        except ValueError:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Use ISO dates for the report range.", "details": {}}}, status=400)
        if date_to < date_from or (date_to - date_from).days > 366:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Choose a valid report range of up to 366 days.", "details": {}}}, status=400)
        all_orders = business.orders.filter(placed_at__date__range=(date_from, date_to))
        orders = all_orders.exclude(status="cancelled")
        sales = orders.aggregate(value=Sum("grand_total"))["value"] or Decimal("0")
        order_items = OrderItem.objects.filter(order__in=orders)
        cost_of_goods = sum(Decimal(str(item.offering_snapshot.get("unit_cost", "0"))) * item.quantity for item in order_items)
        expenses = business.expenses.filter(incurred_at__range=(date_from, date_to))
        expense_total = expenses.aggregate(value=Sum("amount"))["value"] or Decimal("0")
        collected = PaymentAllocation.objects.filter(invoice__business=business, received_at__date__range=(date_from, date_to)).aggregate(value=Sum("amount"))["value"] or Decimal("0")
        inventory_balances = list(business.inventory_balances.select_related("variant"))
        inventory_value = sum(balance.on_hand * balance.variant.unit_cost for balance in inventory_balances)
        quotation_counts = business.quotations.filter(created_at__date__range=(date_from, date_to)).aggregate(
            total=Count("id"),
            converted=Count("id", filter=Q(status="converted")),
            expiring=Count("id", filter=Q(status__in=("draft", "sent"), expires_at__date__lte=timezone.localdate() + timedelta(days=3))),
        )
        aging = business.invoices.exclude(status__in=("paid", "void")).aggregate(
            open_count=Count("id"),
            overdue_count=Count("id", filter=Q(due_at__lt=timezone.localdate())),
            outstanding=Sum(F("grand_total") - F("amount_paid")),
        )
        aging["outstanding"] = aging["outstanding"] or Decimal("0")
        period_purchase_orders = business.purchase_orders.filter(created_at__date__range=(date_from, date_to)).prefetch_related("lines")
        purchase_order_value = sum(
            line.quantity_ordered * line.unit_cost
            for purchase_order in period_purchase_orders
            for line in purchase_order.lines.all()
        )
        sales_by_date = {
            row["placed_at__date"]: row
            for row in orders.values("placed_at__date").annotate(value=Sum("grand_total"), count=Count("id"))
        }
        expenses_by_date = {
            row["incurred_at"]: row["value"] or Decimal("0")
            for row in expenses.values("incurred_at").annotate(value=Sum("amount"))
        }
        daily_activity = []
        current_date = date_from
        while current_date <= date_to:
            daily_activity.append({
                "date": current_date,
                "sales": sales_by_date.get(current_date, {}).get("value", Decimal("0")),
                "orders": sales_by_date.get(current_date, {}).get("count", 0),
                "expenses": expenses_by_date.get(current_date, Decimal("0")),
            })
            current_date += timedelta(days=1)
        expense_breakdown = [
            {"category": row["category__name"], "amount": row["amount"] or Decimal("0")}
            for row in expenses.values("category__name").annotate(amount=Sum("amount")).order_by("-amount")[:8]
        ]
        gross_profit = sales - cost_of_goods
        return Response({
            "range": {"date_from": date_from, "date_to": date_to},
            "currency": business.currency,
            "timezone": timezone.get_current_timezone_name(),
            "sales": sales,
            "orders": {"total": orders.count(), "paid": orders.filter(payment_status="paid").count()},
            "bookings": {"total": business.bookings.filter(starts_at__date__range=(date_from, date_to)).count(), "confirmed": business.bookings.filter(starts_at__date__range=(date_from, date_to), status="confirmed").count()},
            "inventory": {
                "value_at_cost": inventory_value,
                "balances": len(inventory_balances),
                "low_stock_items": sum(1 for balance in inventory_balances if balance.available <= balance.low_stock_threshold),
                "out_of_stock_items": sum(1 for balance in inventory_balances if balance.available <= 0),
                "missing_supplier_items": sum(1 for balance in inventory_balances if not balance.preferred_supplier_id),
            },
            "suppliers": {
                "total": business.suppliers.count(),
                "active": business.suppliers.filter(is_active=True).count(),
            },
            "purchase_orders": {
                "total": period_purchase_orders.count(),
                "open": business.purchase_orders.filter(status__in=("ordered", "partially_received")).count(),
                "overdue": business.purchase_orders.filter(status__in=("ordered", "partially_received"), expected_at__lt=timezone.localdate()).count(),
                "received": period_purchase_orders.filter(status="received").count(),
                "ordered_value": purchase_order_value,
            },
            "quotations": quotation_counts,
            "invoice_aging": aging,
            "collected_payments": collected,
            "expenses": expense_total,
            "expense_evidence": {
                "missing_receipts": expenses.filter(receipt__isnull=True).count(),
                "missing_references": expenses.filter(reference="").count(),
            },
            "daily_activity": daily_activity,
            "expense_breakdown": expense_breakdown,
            "analytics": report_analytics(all_orders, order_items),
            "gross_profit": gross_profit,
            "net_operating_result": gross_profit - expense_total,
            "basis": "Actual recorded transactions only; no forecast values are included.",
        })
