from django.contrib import admin
from .models import ProductReview


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("offering", "author", "rating", "is_visible", "created_at")
    list_filter = ("is_visible", "rating", "offering__business")
    search_fields = ("offering__name", "title", "body")
    readonly_fields = ("offering", "author", "rating", "title", "body", "verified_purchase", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

from .models import Category, Offering, OfferingCostComponent, OfferingFoodProfile, OfferingMedia, OfferingOption, OfferingVariant, OptionGroup, ProductCollection, ProductProfile, VariantDimension, VariantValue


class OfferingVariantInline(admin.TabularInline):
    model = OfferingVariant
    extra = 0


@admin.register(Offering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "offering_type", "status", "base_price")
    list_filter = ("offering_type", "status", "fulfillment_type")
    search_fields = ("name", "sku", "business__display_name")
    inlines = [OfferingVariantInline]


admin.site.register(Category)
admin.site.register(OptionGroup)
admin.site.register(OfferingOption)
admin.site.register(OfferingFoodProfile)
admin.site.register(OfferingCostComponent)
admin.site.register(ProductCollection)
admin.site.register(ProductProfile)
admin.site.register(VariantDimension)
admin.site.register(VariantValue)
admin.site.register(OfferingMedia)
