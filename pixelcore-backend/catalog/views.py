from itertools import product

from django.db import transaction
from django.db.models import Count, F, Max, Min, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.api import BusinessScopedModelViewSet
from businesses.models import Business
from businesses.views import member_business

from .models import Category, Offering, OfferingCostComponent, OfferingFoodProfile, OfferingMedia, OfferingOption, OfferingVariant, OptionGroup, ProductCollection, VariantDimension, VariantValue
from .serializers import CategorySerializer, OfferingCostComponentSerializer, OfferingFoodProfileSerializer, OfferingMediaSerializer, OfferingOptionSerializer, OfferingSerializer, OfferingVariantSerializer, OptionGroupSerializer, ProductCollectionSerializer, PublicOfferingSerializer, PublicProductCollectionSerializer, VariantDimensionSerializer


class CategoryViewSet(BusinessScopedModelViewSet):
    queryset = Category.objects.select_related("parent", "cover_asset")
    serializer_class = CategorySerializer
    audit_resource = "category"


class OfferingViewSet(BusinessScopedModelViewSet):
    queryset = Offering.objects.select_related("category", "product_profile").prefetch_related("variants__option_values", "variants__inventory_balances", "assets", "ordered_media__asset", "ordered_media__variant", "collections", "variant_dimensions__values", "option_groups__options", "cost_components")
    serializer_class = OfferingSerializer
    audit_resource = "offering"

    def get_queryset(self):
        queryset = super().get_queryset()
        for key in ("status", "offering_type", "category__public_id"):
            if self.request.query_params.get(key):
                queryset = queryset.filter(**{key: self.request.query_params[key]})
        search = self.request.query_params.get("search")
        return queryset.filter(name__icontains=search) if search else queryset


class OptionGroupViewSet(BusinessScopedModelViewSet):
    queryset = OptionGroup.objects.select_related("offering").prefetch_related("options")
    serializer_class = OptionGroupSerializer
    audit_resource = "option_group"


class OfferingOptionViewSet(BusinessScopedModelViewSet):
    queryset = OfferingOption.objects.select_related("group", "group__offering")
    serializer_class = OfferingOptionSerializer
    audit_resource = "offering_option"


class OfferingFoodProfileViewSet(BusinessScopedModelViewSet):
    queryset = OfferingFoodProfile.objects.select_related("offering")
    serializer_class = OfferingFoodProfileSerializer
    audit_resource = "food_profile"


class OfferingCostComponentViewSet(BusinessScopedModelViewSet):
    queryset = OfferingCostComponent.objects.select_related("offering")
    serializer_class = OfferingCostComponentSerializer
    audit_resource = "offering_cost_component"


class OfferingVariantListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_offering(self, request, business_public_id, offering_public_id, mutate=False):
        roles = ("owner", "admin", "manager") if mutate else None
        business = member_business(request.user, business_public_id, roles=roles)
        return get_object_or_404(Offering, business=business, public_id=offering_public_id)

    def get(self, request, business_public_id, offering_public_id):
        offering = self.get_offering(request, business_public_id, offering_public_id)
        return Response(OfferingVariantSerializer(offering.variants.all(), many=True).data)

    def post(self, request, business_public_id, offering_public_id):
        offering = self.get_offering(request, business_public_id, offering_public_id, mutate=True)
        serializer = OfferingVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(offering=offering)
        return Response(serializer.data, status=201)


class ProductCollectionViewSet(BusinessScopedModelViewSet):
    queryset = ProductCollection.objects.select_related("cover_asset").prefetch_related("offerings")
    serializer_class = ProductCollectionSerializer
    audit_resource = "product_collection"


class OfferingMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def get_context(self, request, business_public_id, offering_public_id, mutate=False):
        roles = ("owner", "admin", "manager") if mutate else None
        business = member_business(request.user, business_public_id, roles=roles)
        offering = get_object_or_404(Offering, business=business, public_id=offering_public_id)
        return business, offering

    def get(self, request, business_public_id, offering_public_id):
        business, offering = self.get_context(request, business_public_id, offering_public_id)
        serializer = OfferingMediaSerializer(offering.ordered_media.select_related("asset", "variant"), many=True, context={"business": business, "offering": offering, "request": request})
        return Response(serializer.data)

    def post(self, request, business_public_id, offering_public_id):
        business, offering = self.get_context(request, business_public_id, offering_public_id, True)
        serializer = OfferingMediaSerializer(data=request.data, context={"business": business, "offering": offering, "request": request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save(business=business, offering=offering)
        if item.asset not in offering.assets.all():
            offering.assets.add(item.asset)
        return Response(OfferingMediaSerializer(item, context={"business": business, "offering": offering, "request": request}).data, status=201)

    def delete(self, request, business_public_id, offering_public_id, media_public_id):
        business, offering = self.get_context(request, business_public_id, offering_public_id, True)
        get_object_or_404(OfferingMedia, business=business, offering=offering, public_id=media_public_id).delete()
        return Response(status=204)


class VariantMatrixView(APIView):
    permission_classes = [IsAuthenticated]

    def offering(self, request, business_public_id, offering_public_id, mutate=False):
        roles = ("owner", "admin", "manager") if mutate else None
        business = member_business(request.user, business_public_id, roles=roles)
        return business, get_object_or_404(Offering, business=business, public_id=offering_public_id)

    def get(self, request, business_public_id, offering_public_id):
        business, offering = self.offering(request, business_public_id, offering_public_id)
        dimensions = offering.variant_dimensions.prefetch_related("values")
        variants = offering.variants.prefetch_related("option_values")
        return Response({"dimensions": VariantDimensionSerializer(dimensions, many=True).data, "variants": OfferingVariantSerializer(variants, many=True).data, "limits": {"dimensions": 3, "combinations": 100}})

    @transaction.atomic
    def put(self, request, business_public_id, offering_public_id):
        business, offering = self.offering(request, business_public_id, offering_public_id, True)
        dimensions_payload = request.data.get("dimensions") or []
        variants_payload = request.data.get("variants") or []
        if len(dimensions_payload) > 3:
            return Response({"error": {"code": "VARIANT_LIMIT", "message": "A product can have at most three option dimensions.", "details": {}}}, status=400)
        names = [str(item.get("name") or "").strip().lower() for item in dimensions_payload]
        if len(names) != len(set(names)):
            return Response({"error": {"code": "DUPLICATE_DIMENSION", "message": "Option dimension names must be unique.", "details": {}}}, status=400)
        combination_count = 1
        for dimension in dimensions_payload:
            values = dimension.get("values") or []
            if not dimension.get("name") or not values:
                return Response({"error": {"code": "INVALID_MATRIX", "message": "Every option dimension needs a name and at least one value.", "details": {}}}, status=400)
            combination_count *= len(values)
            labels = [str(item.get("label") or "").strip().lower() for item in values]
            if len(labels) != len(set(labels)):
                return Response({"error": {"code": "DUPLICATE_OPTION", "message": f"{dimension.get('name')} values must be unique.", "details": {}}}, status=400)
        if combination_count > 100:
            return Response({"error": {"code": "VARIANT_LIMIT", "message": "This matrix would create more than 100 combinations.", "details": {"combinations": combination_count}}}, status=400)
        if dimensions_payload and len(variants_payload) != combination_count:
            return Response({"error": {"code": "INCOMPLETE_MATRIX", "message": "Send one variant row for every generated option combination.", "details": {"expected": combination_count}}}, status=400)

        offering.variant_dimensions.all().delete()
        created_dimensions = []
        value_by_label = {}
        for index, raw_dimension in enumerate(dimensions_payload):
            dimension = VariantDimension.objects.create(business=business, offering=offering, name=str(raw_dimension["name"]).strip()[:80], display_type=raw_dimension.get("display_type") if raw_dimension.get("display_type") in {"text", "color"} else "text", sort_order=index)
            created_dimensions.append(dimension)
            for value_index, raw_value in enumerate(raw_dimension.get("values") or []):
                swatch = str(raw_value.get("swatch_color") or "")
                value_serializer = VariantDimensionSerializer(data={"name": dimension.name, "display_type": dimension.display_type, "sort_order": index, "values": [{"label": str(raw_value.get("label") or "").strip(), "swatch_color": swatch, "sort_order": value_index}]})
                value_serializer.is_valid(raise_exception=True)
                value = VariantValue.objects.create(business=business, dimension=dimension, label=str(raw_value.get("label") or "").strip()[:100], swatch_color=swatch.lower(), sort_order=value_index)
                value_by_label[(dimension.name.lower(), value.label.lower())] = value

        desired_keys = set()
        for index, raw_variant in enumerate(variants_payload):
            selected = raw_variant.get("options") or {}
            values = []
            for dimension in created_dimensions:
                value = value_by_label.get((dimension.name.lower(), str(selected.get(dimension.name, "")).strip().lower()))
                if not value:
                    return Response({"error": {"code": "INVALID_MATRIX", "message": f"Choose a valid {dimension.name} value for every variant.", "details": {}}}, status=400)
                values.append(value)
            key = "|".join(str(value.public_id) for value in values)
            if key in desired_keys:
                return Response({"error": {"code": "DUPLICATE_COMBINATION", "message": "Each option combination must be unique.", "details": {}}}, status=400)
            desired_keys.add(key)
            variant = offering.variants.filter(public_id=raw_variant.get("public_id")).first()
            if not variant:
                variant = OfferingVariant(offering=offering)
            variant.name = " / ".join(value.label for value in values) or str(raw_variant.get("name") or "Default")
            variant.sku = str(raw_variant.get("sku") or "")[:80]
            variant.barcode = str(raw_variant.get("barcode") or "")[:120]
            variant.price = raw_variant.get("price", offering.base_price)
            variant.compare_at_price = raw_variant.get("compare_at_price") or None
            variant.unit_cost = raw_variant.get("unit_cost", 0)
            variant.is_active = bool(raw_variant.get("is_active", True))
            variant.sort_order = index
            variant.combination_key = key
            variant.attributes = {value.dimension.name: value.label for value in values}
            variant.save()
            variant.option_values.set(values)
        offering.variants.exclude(combination_key__in=desired_keys).exclude(combination_key="").delete()
        return self.get(request, business_public_id, offering_public_id)


class CommercePagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 60

    def get_paginated_response(self, data, facets, highlighted=None):
        return Response({"count": self.page.paginator.count, "next": self.get_next_link(), "previous": self.get_previous_link(), "results": data, "facets": facets, "highlighted": highlighted})


def public_product_queryset(business):
    return business.offerings.filter(status="published").exclude(offering_type="service").annotate(
        active_reservation_count=Count(
            "product_requests__email",
            filter=Q(
                product_requests__kind="reservation",
                product_requests__status="held",
                product_requests__expires_at__gt=timezone.now(),
            ),
            distinct=True,
        ),
    ).select_related("category", "product_profile").prefetch_related("variants__option_values__dimension", "variants__inventory_balances", "assets", "ordered_media__asset", "ordered_media__variant", "collections", "variant_dimensions__values", "option_groups__options")


class PublicCommerceProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        queryset = public_product_queryset(business)
        highlighted = queryset.filter(product_profile__storefront_highlighted=True).first()
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(summary__icontains=search) | Q(product_profile__brand__icontains=search) | Q(product_profile__tags__icontains=search))
        if request.query_params.get("category"):
            queryset = queryset.filter(category__slug=request.query_params["category"])
        if request.query_params.get("collection"):
            queryset = queryset.filter(collections__slug=request.query_params["collection"], collections__is_published=True)
        if request.query_params.get("tag"):
            queryset = queryset.filter(product_profile__tags__contains=[request.query_params["tag"]])
        if request.query_params.get("price_min"):
            queryset = queryset.filter(base_price__gte=request.query_params["price_min"])
        if request.query_params.get("price_max"):
            queryset = queryset.filter(base_price__lte=request.query_params["price_max"])
        if request.query_params.get("option_value"):
            queryset = queryset.filter(variants__option_values__public_id=request.query_params["option_value"])
        if request.query_params.get("availability") == "in_stock":
            queryset = queryset.filter(Q(track_inventory=False) | Q(variants__inventory_balances__on_hand__gt=F("variants__inventory_balances__reserved")))
        orderings = {"newest": "-created_at", "price_low": "base_price", "price_high": "-base_price", "name": "name"}
        queryset = queryset.order_by(orderings.get(request.query_params.get("ordering"), "-created_at")).distinct()
        facets = {
            "categories": [
                {
                    "public_id": str(category.public_id),
                    "name": category.name,
                    "slug": category.slug,
                    "show_in_header": category.show_in_header,
                    "header_order": category.header_order,
                    "image": category.cover_asset.file.url if category.cover_asset_id else "",
                }
                for category in business.categories.filter(is_active=True, offerings__status="published").select_related("cover_asset").distinct().order_by("header_order", "sort_order", "name")
            ],
            "collections": list(business.product_collections.filter(is_published=True).values("name", "slug")),
            "price": queryset.aggregate(min=Min("base_price"), max=Max("base_price")),
        }
        paginator = CommercePagination()
        page = paginator.paginate_queryset(queryset, request)
        highlighted_data = PublicOfferingSerializer(highlighted, context={"request": request}).data if highlighted else None
        return paginator.get_paginated_response(PublicOfferingSerializer(page, many=True, context={"request": request}).data, facets, highlighted_data)


class PublicCommerceProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, offering_slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        offering = get_object_or_404(public_product_queryset(business), slug=offering_slug)
        data = PublicOfferingSerializer(offering, context={"request": request}).data
        related = public_product_queryset(business).exclude(pk=offering.pk)
        if offering.category_id:
            related = related.filter(category_id=offering.category_id)
        data["related_products"] = PublicOfferingSerializer(related[:4], many=True, context={"request": request}).data
        from .reviews import review_summary
        data["review_summary"] = review_summary(offering)
        return Response(data)


class PublicCollectionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, collection_slug=None):
        business = get_object_or_404(Business, slug=slug, status="active")
        queryset = business.product_collections.filter(is_published=True).select_related("cover_asset").prefetch_related("offerings")
        if collection_slug:
            collection = get_object_or_404(queryset, slug=collection_slug)
            return Response(PublicProductCollectionSerializer(collection, context={"request": request}).data)
        return Response(PublicProductCollectionSerializer(queryset, many=True, context={"request": request}).data)


class PublicCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, status="active")
        offerings = business.offerings.filter(status="published").select_related("category").prefetch_related("variants", "assets", "option_groups__options")
        offering_type = request.query_params.get("type")
        if offering_type:
            offerings = offerings.filter(offering_type=offering_type)
        return Response(PublicOfferingSerializer(offerings, many=True, context={"request": request}).data)


class PublicOfferingDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, offering_slug):
        offering = get_object_or_404(
            Offering.objects.select_related("business", "category").prefetch_related("variants", "assets"),
            business__slug=slug,
            business__status="active",
            slug=offering_slug,
            status="published",
        )
        return Response(PublicOfferingSerializer(offering, context={"request": request}).data)
