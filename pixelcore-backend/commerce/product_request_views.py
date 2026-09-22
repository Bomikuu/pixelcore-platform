from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from businesses.api import BusinessScopedReadOnlyViewSet
from businesses.models import Business
from businesses.services import record_audit
from businesses.views import member_business
from .models import ProductRequest, ProductRequestSettings
from .live_sales import LivePagination, request_counts, request_scopes
from .product_requests import (
    ProductRequestInput, ProductRequestSerializer, ProductRequestSettingsSerializer,
    create_product_request, expire_business_requests, public_request_result, transition_product_request,
)


class ProductRequestThrottle(SimpleRateThrottle):
    scope = "product_requests"
    rate = "10/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": f'{view.kwargs["slug"]}:{self.get_ident(request)}'}


class PublicProductRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ProductRequestThrottle]

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        serializer = ProductRequestInput(data=request.data, context={"business": business})
        serializer.is_valid(raise_exception=True)
        expire_business_requests(business.pk)
        item, created = create_product_request(business, serializer.validated_data)
        return Response(public_request_result(item), status=201 if created else 200)


class ProductRequestSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_public_id):
        business = member_business(request.user, business_public_id, roles=("owner", "admin", "manager"))
        config = ProductRequestSettings.objects.filter(business=business).first() or ProductRequestSettings(business=business)
        return Response(ProductRequestSettingsSerializer(config).data)

    def put(self, request, business_public_id):
        business = member_business(request.user, business_public_id, roles=("owner", "admin", "manager"))
        config = ProductRequestSettings.objects.filter(business=business).first() or ProductRequestSettings(business=business)
        serializer = ProductRequestSettingsSerializer(config, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit(business, request.user, "product_request.settings_updated", "business", business.public_id)
        return Response(serializer.data)


class ProductRequestViewSet(BusinessScopedReadOnlyViewSet):
    queryset = ProductRequest.objects.select_related("location", "order", "business")
    serializer_class = ProductRequestSerializer
    pagination_class = LivePagination

    def get_business(self):
        return member_business(self.request.user, self.kwargs["business_public_id"], roles=("owner", "admin", "manager"))

    def get_queryset(self):
        business = self.get_business()
        expire_business_requests(business.pk)
        queryset = super().get_queryset()
        scope = self.request.query_params.get('scope', 'all')
        scopes = request_scopes(business)
        if scope not in scopes:
            raise serializers.ValidationError({'scope': 'Choose a supported request view.'})
        queryset = queryset.filter(scopes[scope])
        search = self.request.query_params.get('search', '').strip()[:120]
        if search:
            queryset = queryset.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search) | Q(snapshot__name__icontains=search))
        if self.request.query_params.get("status"):
            queryset = queryset.filter(status=self.request.query_params["status"])
        if self.request.query_params.get("kind"):
            queryset = queryset.filter(kind=self.request.query_params["kind"])
        return queryset.order_by('ends_on', 'created_at', 'id') if scope in {'overdue', 'due_today'} else queryset

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['summary'] = request_counts(self.get_business())
        return response

    def transition(self, request, business_public_id, public_id):
        class ActionInput(serializers.Serializer):
            action = serializers.ChoiceField(choices=["approve", "reject", "cancel", "collect", "return", "convert", "extend", "follow_up"])
            note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
            ends_on = serializers.DateField(required=False)
            expected_updated_at = serializers.DateTimeField(required=False)
        data = ActionInput(data=request.data)
        data.is_valid(raise_exception=True)
        business = self.get_business()
        expire_business_requests(business.pk)
        item = transition_product_request(business, public_id, actor=request.user, **data.validated_data)
        return Response(self.get_serializer(item).data)
