from django.urls import path
from .reviews import MyProductReviewView, ProductReviewsView

from .views import CategoryViewSet, CommercePagination, OfferingCostComponentViewSet, OfferingFoodProfileViewSet, OfferingMediaView, OfferingOptionViewSet, OfferingVariantListCreateView, OfferingViewSet, OptionGroupViewSet, ProductCollectionViewSet, PublicCatalogView, PublicCollectionsView, PublicCommerceProductDetailView, PublicCommerceProductsView, PublicOfferingDetailView, VariantMatrixView


category_list = CategoryViewSet.as_view({"get": "list", "post": "create"})
category_detail = CategoryViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
offering_list = OfferingViewSet.as_view({"get": "list", "post": "create"})
offering_detail = OfferingViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
collection_list = ProductCollectionViewSet.as_view({"get": "list", "post": "create"})
collection_detail = ProductCollectionViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("public/<slug:slug>/storefront/products/<slug:offering_slug>/reviews/", ProductReviewsView.as_view()),
    path("public/<slug:slug>/storefront/products/<slug:offering_slug>/reviews/mine/", MyProductReviewView.as_view()),
    path("businesses/<uuid:business_public_id>/categories/", category_list),
    path("businesses/<uuid:business_public_id>/categories/<uuid:public_id>/", category_detail),
    path("businesses/<uuid:business_public_id>/offerings/", offering_list),
    path("businesses/<uuid:business_public_id>/offerings/<uuid:public_id>/", offering_detail),
    path("businesses/<uuid:business_public_id>/offerings/<uuid:offering_public_id>/variants/", OfferingVariantListCreateView.as_view()),
    path("businesses/<uuid:business_public_id>/offerings/<uuid:offering_public_id>/variant-matrix/", VariantMatrixView.as_view()),
    path("businesses/<uuid:business_public_id>/offerings/<uuid:offering_public_id>/media/", OfferingMediaView.as_view()),
    path("businesses/<uuid:business_public_id>/offerings/<uuid:offering_public_id>/media/<uuid:media_public_id>/", OfferingMediaView.as_view()),
    path("businesses/<uuid:business_public_id>/collections/", collection_list),
    path("businesses/<uuid:business_public_id>/collections/<uuid:public_id>/", collection_detail),
    path("businesses/<uuid:business_public_id>/option-groups/", OptionGroupViewSet.as_view({"get": "list", "post": "create"})),
    path("businesses/<uuid:business_public_id>/option-groups/<uuid:public_id>/", OptionGroupViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("businesses/<uuid:business_public_id>/offering-options/", OfferingOptionViewSet.as_view({"get": "list", "post": "create"})),
    path("businesses/<uuid:business_public_id>/offering-options/<uuid:public_id>/", OfferingOptionViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("businesses/<uuid:business_public_id>/food-profiles/", OfferingFoodProfileViewSet.as_view({"get": "list", "post": "create"})),
    path("businesses/<uuid:business_public_id>/food-profiles/<uuid:public_id>/", OfferingFoodProfileViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("businesses/<uuid:business_public_id>/offering-costs/", OfferingCostComponentViewSet.as_view({"get": "list", "post": "create"})),
    path("businesses/<uuid:business_public_id>/offering-costs/<uuid:public_id>/", OfferingCostComponentViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("public/<slug:slug>/catalog/", PublicCatalogView.as_view()),
    path("public/<slug:slug>/catalog/<slug:offering_slug>/", PublicOfferingDetailView.as_view()),
    path("public/<slug:slug>/storefront/products/", PublicCommerceProductsView.as_view()),
    path("public/<slug:slug>/storefront/products/<slug:offering_slug>/", PublicCommerceProductDetailView.as_view()),
    path("public/<slug:slug>/storefront/collections/", PublicCollectionsView.as_view()),
    path("public/<slug:slug>/storefront/collections/<slug:collection_slug>/", PublicCollectionsView.as_view()),
]
