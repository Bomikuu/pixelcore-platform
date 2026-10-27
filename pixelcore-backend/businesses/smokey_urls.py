from django.urls import path
from .smokey_views import (
    SmokeySettingsView,
    SmokeyConnectionsView,
    SmokeyConnectionView,
    SmokeyModelsView,
    SmokeyModelDiscoveryView,
    SmokeyConnectionCheckView,
    SmokeyGenerationListView,
    SmokeyGenerationView,
    SmokeyCancelView,
    SmokeyReportsView,
    SmokeyReportView,
    SmokeyReportRowsView,
    SmokeyUsageView,
    SmokeyAssetView,
)

urlpatterns = [
    path("models/", SmokeyModelDiscoveryView.as_view()),
    path("settings/", SmokeySettingsView.as_view()),
    path("connections/", SmokeyConnectionsView.as_view()),
    path("connections/<uuid:connection_id>/", SmokeyConnectionView.as_view()),
    path("connections/<uuid:connection_id>/models/", SmokeyModelsView.as_view()),
    path(
        "connections/<uuid:connection_id>/check/", SmokeyConnectionCheckView.as_view()
    ),
    path("generations/", SmokeyGenerationListView.as_view()),
    path("generations/<uuid:generation_id>/", SmokeyGenerationView.as_view()),
    path("generations/<uuid:generation_id>/cancel/", SmokeyCancelView.as_view()),
    path("reports/", SmokeyReportsView.as_view()),
    path("reports/<uuid:report_id>/", SmokeyReportView.as_view()),
    path(
        "reports/<uuid:report_id>/tables/<str:table_key>/",
        SmokeyReportRowsView.as_view(),
    ),
    path("usage/", SmokeyUsageView.as_view()),
    path("asset/", SmokeyAssetView.as_view()),
]
