from django.urls import path
from .live_sales import LiveSalesView
from .product_request_views import PublicProductRequestView, ProductRequestSettingsView, ProductRequestViewSet

from .views import (
    CustomerViewSet, OrderViewSet, PayMongoWebhookView, PaymentConnectionView, PublicCartCreateView,
    PublicCartDetailView, PublicCartItemView, PublicCheckoutView, PublicShippingZoneListView, ShippingZoneViewSet,
    PublicDigitalDownloadView, CustomerPortalAddressView, CustomerPortalView, CustomerSavedOfferingView, DiscountViewSet,
    PosCheckoutView, PublicCustomerDisplayView, PublicOrderConfirmationView, CustomerSavedOfferingMergeView, DeviceOrderPaymentView, DeviceOrderQueueView, DeviceOrderStatusView, DevicePosAuthorizationView, DevicePosCheckoutView, DevicePosSessionView, DevicePosHoldView, DevicePosHoldResumeView, DevicePosVoidView, DevicePosTransactionView, DevicePosReceiptView, DevicePosRefundView,
)

customer_list = CustomerViewSet.as_view({"get": "list", "post": "create"})
customer_detail = CustomerViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
order_list = OrderViewSet.as_view({"get": "list"})
order_detail = OrderViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
zone_list = ShippingZoneViewSet.as_view({"get": "list", "post": "create"})
zone_detail = ShippingZoneViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
discount_list = DiscountViewSet.as_view({"get": "list", "post": "create"})
discount_detail = DiscountViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("businesses/<uuid:business_public_id>/live-sales/", LiveSalesView.as_view()),
    path("public/<slug:slug>/product-requests/", PublicProductRequestView.as_view()),
    path("businesses/<uuid:business_public_id>/product-request-settings/", ProductRequestSettingsView.as_view()),
    path("businesses/<uuid:business_public_id>/product-requests/", ProductRequestViewSet.as_view({"get": "list"})),
    path("businesses/<uuid:business_public_id>/product-requests/<uuid:public_id>/", ProductRequestViewSet.as_view({"get": "retrieve"})),
    path("businesses/<uuid:business_public_id>/product-requests/<uuid:public_id>/transition/", ProductRequestViewSet.as_view({"post": "transition"})),
    path("businesses/<uuid:business_public_id>/customers/", customer_list),
    path("businesses/<uuid:business_public_id>/customers/<uuid:public_id>/", customer_detail),
    path("businesses/<uuid:business_public_id>/orders/", order_list),
    path("businesses/<uuid:business_public_id>/orders/<uuid:public_id>/", order_detail),
    path("businesses/<uuid:business_public_id>/shipping-zones/", zone_list),
    path("businesses/<uuid:business_public_id>/shipping-zones/<uuid:public_id>/", zone_detail),
    path("businesses/<uuid:business_public_id>/discounts/", discount_list),
    path("businesses/<uuid:business_public_id>/discounts/<uuid:public_id>/", discount_detail),
    path("businesses/<uuid:public_id>/pos/checkout/", PosCheckoutView.as_view()),
    path("businesses/<uuid:public_id>/payments/connections/", PaymentConnectionView.as_view()),
    path("businesses/<uuid:public_id>/payments/connections/<str:provider>/", PaymentConnectionView.as_view()),
    path("public/<slug:slug>/carts/", PublicCartCreateView.as_view()),
    path("public/<slug:slug>/carts/<uuid:cart_id>/", PublicCartDetailView.as_view()),
    path("public/<slug:slug>/carts/<uuid:cart_id>/items/", PublicCartItemView.as_view()),
    path("public/<slug:slug>/carts/<uuid:cart_id>/items/<uuid:item_id>/", PublicCartItemView.as_view()),
    path("public/<slug:slug>/carts/<uuid:cart_id>/checkout/", PublicCheckoutView.as_view()),
    path("public/<slug:slug>/shipping-zones/", PublicShippingZoneListView.as_view()),
    path("public/downloads/", PublicDigitalDownloadView.as_view()),
    path("public/<slug:slug>/portal/", CustomerPortalView.as_view()),
    path("public/<slug:slug>/portal/addresses/", CustomerPortalAddressView.as_view()),
    path("public/<slug:slug>/portal/addresses/<uuid:address_id>/", CustomerPortalAddressView.as_view()),
    path("public/<slug:slug>/portal/saved/merge/", CustomerSavedOfferingMergeView.as_view()),
    path("public/<slug:slug>/portal/saved/", CustomerSavedOfferingView.as_view()),
    path("public/<slug:slug>/portal/saved/<uuid:offering_id>/", CustomerSavedOfferingView.as_view()),
    path("public/<slug:slug>/orders/<uuid:order_id>/", PublicOrderConfirmationView.as_view()),
    path("public/devices/customer-display/", PublicCustomerDisplayView.as_view()),
    path("devices/orders/queue/", DeviceOrderQueueView.as_view()),
    path("devices/orders/<uuid:order_id>/status/", DeviceOrderStatusView.as_view()),
    path("devices/orders/<uuid:order_id>/payment/", DeviceOrderPaymentView.as_view()),
    path("devices/pos/authorize/", DevicePosAuthorizationView.as_view()),
    path("devices/pos/holds/", DevicePosHoldView.as_view()),
    path("devices/pos/holds/<uuid:hold_id>/resume/", DevicePosHoldResumeView.as_view()),
    path("devices/pos/void/", DevicePosVoidView.as_view()),
    path("devices/pos/transactions/", DevicePosTransactionView.as_view()),
    path("devices/pos/transactions/<uuid:order_id>/receipt/", DevicePosReceiptView.as_view()),
    path("devices/pos/transactions/<uuid:order_id>/refund/", DevicePosRefundView.as_view()),
    path("devices/pos/checkout/", DevicePosCheckoutView.as_view()),
    path("devices/pos/session/", DevicePosSessionView.as_view()),
    path("public/payments/paymongo/<uuid:business_id>/webhook/", PayMongoWebhookView.as_view()),
]
