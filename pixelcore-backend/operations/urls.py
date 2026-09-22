from django.urls import path

from .views import (
    BusinessReportView, ExpenseCategoryViewSet, ExpenseViewSet, InventoryAdjustView, InventoryBalanceViewSet,
    InventoryTransferView, InvoicePaymentAllocationView, InvoicePdfView, InvoiceViewSet, PublicQuotationAcceptanceView,
    PurchaseOrderReceiveView, PurchaseOrderViewSet, QuotationViewSet, StockMovementViewSet, SupplierViewSet,
    SupplierProductViewSet,
)


def model_routes(prefix, viewset, detail_methods=None):
    detail_methods = detail_methods or {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
    return [
        path(f"businesses/<uuid:business_public_id>/{prefix}/", viewset.as_view({"get": "list", "post": "create"})),
        path(f"businesses/<uuid:business_public_id>/{prefix}/<uuid:public_id>/", viewset.as_view(detail_methods)),
    ]


urlpatterns = []
urlpatterns += model_routes("inventory", InventoryBalanceViewSet, {"get": "retrieve", "patch": "partial_update"})
urlpatterns += [
    path("businesses/<uuid:business_public_id>/stock-movements/", StockMovementViewSet.as_view({"get": "list"})),
    path("businesses/<uuid:business_public_id>/stock-movements/<uuid:public_id>/", StockMovementViewSet.as_view({"get": "retrieve"})),
]
urlpatterns += model_routes("suppliers", SupplierViewSet)
urlpatterns += model_routes("supplier-products", SupplierProductViewSet)
urlpatterns += model_routes("purchase-orders", PurchaseOrderViewSet)
urlpatterns += model_routes("quotations", QuotationViewSet)
urlpatterns += model_routes("invoices", InvoiceViewSet)
urlpatterns += model_routes("expense-categories", ExpenseCategoryViewSet)
urlpatterns += model_routes("expenses", ExpenseViewSet)
urlpatterns += [
    path("businesses/<uuid:public_id>/inventory/<uuid:balance_id>/adjust/", InventoryAdjustView.as_view()),
    path("businesses/<uuid:public_id>/inventory/transfer/", InventoryTransferView.as_view()),
    path("businesses/<uuid:public_id>/purchase-orders/<uuid:purchase_order_id>/receive/", PurchaseOrderReceiveView.as_view()),
    path("businesses/<uuid:public_id>/invoices/<uuid:invoice_id>/payments/", InvoicePaymentAllocationView.as_view()),
    path("businesses/<uuid:public_id>/invoices/<uuid:invoice_id>/pdf/", InvoicePdfView.as_view()),
    path("businesses/<uuid:public_id>/reports/", BusinessReportView.as_view()),
    path("public/<slug:slug>/quotations/<uuid:quotation_id>/", PublicQuotationAcceptanceView.as_view()),
]
