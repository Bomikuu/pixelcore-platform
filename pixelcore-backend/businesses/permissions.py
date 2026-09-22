from rest_framework.permissions import BasePermission


class CanManageBusiness(BasePermission):
    message = "Only business owners and administrators can change this identity."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.memberships.filter(
            user=request.user,
            status="active",
            role__in=("owner", "admin"),
        ).exists()
