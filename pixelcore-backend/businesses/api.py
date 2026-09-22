from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .services import record_audit
from .views import member_business


class BusinessScopedModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    business_roles = ("owner", "admin", "manager", "staff")
    mutation_roles = ("owner", "admin", "manager")
    audit_resource = "resource"

    def get_business(self):
        if not hasattr(self, "_business"):
            roles = self.mutation_roles if self.action not in {"list", "retrieve"} else self.business_roles
            self._business = member_business(self.request.user, self.kwargs["business_public_id"], roles=roles)
        return self._business

    def get_queryset(self):
        return super().get_queryset().filter(business=self.get_business())

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "business": self.get_business()}

    def perform_create(self, serializer):
        instance = serializer.save(business=self.get_business())
        record_audit(self.get_business(), self.request.user, f"{self.audit_resource}.created", self.audit_resource, instance.public_id)

    def perform_update(self, serializer):
        instance = serializer.save()
        record_audit(self.get_business(), self.request.user, f"{self.audit_resource}.updated", self.audit_resource, instance.public_id)

    def perform_destroy(self, instance):
        resource_id = instance.public_id
        instance.delete()
        record_audit(self.get_business(), self.request.user, f"{self.audit_resource}.deleted", self.audit_resource, resource_id)


class BusinessScopedReadOnlyViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def get_business(self):
        if not hasattr(self, "_business"):
            self._business = member_business(self.request.user, self.kwargs["business_public_id"])
        return self._business

    def get_queryset(self):
        return super().get_queryset().filter(business=self.get_business())

