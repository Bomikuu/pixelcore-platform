from django.urls import path
from .views import CustomerTracking, OwnerDeliveries, OwnerDelivery, OwnerRider, OwnerRiders, RiderAccept, RiderDeliveries, RiderDelivery, RiderLocation

urlpatterns = [
    path("businesses/<uuid:business_public_id>/deliveries/", OwnerDeliveries.as_view()),
    path("businesses/<uuid:business_public_id>/deliveries/<uuid:public_id>/", OwnerDelivery.as_view()),
    path("businesses/<uuid:business_public_id>/delivery-riders/", OwnerRiders.as_view()),
    path("businesses/<uuid:business_public_id>/delivery-riders/<uuid:public_id>/", OwnerRider.as_view()),
    path("rider/deliveries/", RiderDeliveries.as_view()),
    path("rider/access/<uuid:public_id>/accept/", RiderAccept.as_view()),
    path("rider/deliveries/<uuid:public_id>/", RiderDelivery.as_view()),
    path("rider/deliveries/<uuid:public_id>/location/", RiderLocation.as_view()),
    path("public/<slug:slug>/orders/<uuid:order_id>/tracking/", CustomerTracking.as_view()),
]
