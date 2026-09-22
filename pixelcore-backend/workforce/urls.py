from django.urls import path

from .views import (
    AttendanceFlagViewSet,
    AttendanceRecordViewSet,
    AttendanceTerminalView,
    EmployeeAdminSummaryView,
    EmployeeAttendanceCodeView,
    EmployeeAttendancePinView,
    EmployeeLeaveCancelView,
    EmployeeLeaveRequestView,
    EmployeePortalView,
    LeaveRequestViewSet,
    StaffAttendancePinView,
    StaffDocumentViewSet,
)


def routes(prefix, viewset, detail=None):
    detail = detail or {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
    return [
        path(f"businesses/<uuid:business_public_id>/workforce/{prefix}/", viewset.as_view({"get": "list", "post": "create"})),
        path(f"businesses/<uuid:business_public_id>/workforce/{prefix}/<uuid:public_id>/", viewset.as_view(detail)),
    ]


urlpatterns = []
urlpatterns += routes("documents", StaffDocumentViewSet)
urlpatterns += routes("attendance", AttendanceRecordViewSet, {"get": "retrieve", "patch": "partial_update"})
urlpatterns += routes("leave-requests", LeaveRequestViewSet)
urlpatterns += routes("attendance-flags", AttendanceFlagViewSet, {"get": "retrieve", "patch": "partial_update"})
urlpatterns += [
    path("businesses/<uuid:business_public_id>/workforce/documents/<uuid:public_id>/review/", StaffDocumentViewSet.as_view({"post": "review"})),
    path("businesses/<uuid:public_id>/workforce/staff/<uuid:staff_id>/attendance-pin/", StaffAttendancePinView.as_view()),
    path("businesses/<uuid:public_id>/workforce/employees/<uuid:staff_id>/summary/", EmployeeAdminSummaryView.as_view()),
    path("businesses/<uuid:public_id>/workforce/me/", EmployeePortalView.as_view()),
    path("businesses/<uuid:public_id>/workforce/me/attendance-code/", EmployeeAttendanceCodeView.as_view()),
    path("businesses/<uuid:public_id>/workforce/me/attendance-pin/", EmployeeAttendancePinView.as_view()),
    path("businesses/<uuid:public_id>/workforce/me/leave-requests/", EmployeeLeaveRequestView.as_view()),
    path("businesses/<uuid:public_id>/workforce/me/leave-requests/<uuid:leave_id>/cancel/", EmployeeLeaveCancelView.as_view()),
    path("devices/attendance/", AttendanceTerminalView.as_view()),
]
