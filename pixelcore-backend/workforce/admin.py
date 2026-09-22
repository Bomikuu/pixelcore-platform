from django.contrib import admin

from .models import (
    AttendanceActionCode,
    AttendanceFlag,
    AttendanceRecord,
    LeaveRequest,
    StaffDocument,
)


admin.site.register(StaffDocument)
admin.site.register(AttendanceRecord)
admin.site.register(LeaveRequest)
admin.site.register(AttendanceFlag)
admin.site.register(AttendanceActionCode)
