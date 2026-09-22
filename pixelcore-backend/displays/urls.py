from django.urls import path
from .views import DisplayDeviceSessionView, DisplayPublicationViewSet, PublicDisplayView

list_view = DisplayPublicationViewSet.as_view({"get": "list", "post": "create"})
detail_view = DisplayPublicationViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
urlpatterns = [
    path("businesses/<uuid:business_public_id>/displays/", list_view),
    path("businesses/<uuid:business_public_id>/displays/<uuid:public_id>/", detail_view),
    path("businesses/<uuid:business_public_id>/displays/<uuid:public_id>/publish/", DisplayPublicationViewSet.as_view({"post": "publish"})),
    path("businesses/<uuid:business_public_id>/displays/<uuid:public_id>/assign-device/", DisplayPublicationViewSet.as_view({"post": "assign_device"})),
    path("public/displays/<uuid:share_key>/", PublicDisplayView.as_view()),
    path("devices/displays/session/", DisplayDeviceSessionView.as_view()),
]
