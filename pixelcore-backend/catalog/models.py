import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from businesses.models import Business, BusinessAsset


class ProductReview(models.Model):
    """One purchase-backed review per account and product; content is plain text."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    offering = models.ForeignKey("Offering", on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=120)
    body = models.TextField(max_length=3000)
    verified_purchase = models.BooleanField(default=False, editable=False)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["offering", "author"], name="unique_product_review_author"),
            models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="product_review_rating_range"),
        ]
        indexes = [models.Index(fields=["offering", "is_visible", "-created_at"], name="product_review_public_idx")]


def unique_slug(model, business, value, instance=None):
    base = slugify(value)[:140] or "item"
    candidate = base
    suffix = 2
    queryset = model.objects.filter(business=business)
    if instance:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=candidate).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


class Category(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=160, blank=True)
    description = models.TextField(blank=True, max_length=1000)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="children")
    cover_asset = models.ForeignKey(BusinessAsset, on_delete=models.SET_NULL, blank=True, null=True, related_name="covered_categories")
    sort_order = models.PositiveIntegerField(default=0)
    show_in_header = models.BooleanField(default=True)
    header_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "slug"], name="unique_business_category_slug")]
        ordering = ["sort_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.business, self.name, self)
        super().save(*args, **kwargs)


class Offering(models.Model):
    TYPE_CHOICES = [("physical", "Physical product"), ("digital", "Digital product"), ("service", "Service")]
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published"), ("archived", "Archived")]
    FULFILLMENT_CHOICES = [
        ("delivery", "Delivery"), ("pickup", "Pickup"), ("digital", "Digital delivery"),
        ("booking", "Booking"), ("none", "No fulfillment"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="offerings")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name="offerings")
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, blank=True)
    summary = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True, max_length=8000)
    offering_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    fulfillment_type = models.CharField(max_length=16, choices=FULFILLMENT_CHOICES, default="none")
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    sku = models.CharField(max_length=80, blank=True)
    track_inventory = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=1)
    assets = models.ManyToManyField(BusinessAsset, blank=True, related_name="offerings")
    digital_asset = models.ForeignKey(BusinessAsset, on_delete=models.SET_NULL, blank=True, null=True, related_name="digital_offerings")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "slug"], name="unique_business_offering_slug")]
        ordering = ["name", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Offering, self.business, self.name, self)
        if self.offering_type == "service":
            self.fulfillment_type = "booking"
            self.track_inventory = False
        super().save(*args, **kwargs)


class ProductCollection(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="product_collections")
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, blank=True)
    description = models.TextField(blank=True, max_length=2000)
    cover_asset = models.ForeignKey(BusinessAsset, on_delete=models.SET_NULL, blank=True, null=True, related_name="covered_product_collections")
    offerings = models.ManyToManyField(Offering, blank=True, related_name="collections")
    hero_settings = models.JSONField(default=dict, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "slug"], name="unique_business_product_collection_slug")]
        ordering = ["sort_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(ProductCollection, self.business, self.name, self)
        super().save(*args, **kwargs)


class ProductProfile(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="product_profiles")
    offering = models.OneToOneField(Offering, on_delete=models.CASCADE, related_name="product_profile")
    brand = models.CharField(max_length=140, blank=True)
    tags = models.JSONField(default=list, blank=True)
    materials = models.TextField(blank=True, max_length=4000)
    care_instructions = models.TextField(blank=True, max_length=4000)
    shipping_weight_grams = models.PositiveIntegerField(blank=True, null=True)
    shipping_dimensions = models.JSONField(default=dict, blank=True)
    size_guide = models.JSONField(default=dict, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    card_hover_enabled = models.BooleanField(default=True)
    card_gallery_enabled = models.BooleanField(default=False)
    storefront_highlighted = models.BooleanField(default=False)
    reservation_enabled = models.BooleanField(default=False)
    rental_enabled = models.BooleanField(default=False)
    reservation_terms = models.TextField(blank=True, max_length=2000)
    rental_terms = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business"],
                condition=Q(storefront_highlighted=True),
                name="unique_business_storefront_highlight",
            )
        ]


class VariantDimension(models.Model):
    DISPLAY_CHOICES = [("text", "Text"), ("color", "Color")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="variant_dimensions")
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="variant_dimensions")
    name = models.CharField(max_length=80)
    display_type = models.CharField(max_length=12, choices=DISPLAY_CHOICES, default="text")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["offering", "name"], name="unique_offering_variant_dimension")]
        ordering = ["sort_order", "id"]


class VariantValue(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="variant_values")
    dimension = models.ForeignKey(VariantDimension, on_delete=models.CASCADE, related_name="values")
    label = models.CharField(max_length=100)
    swatch_color = models.CharField(max_length=7, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["dimension", "label"], name="unique_dimension_variant_value")]
        ordering = ["sort_order", "id"]


class OfferingVariant(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=80, blank=True)
    barcode = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    attributes = models.JSONField(default=dict, blank=True)
    combination_key = models.CharField(max_length=255, blank=True)
    option_values = models.ManyToManyField(VariantValue, blank=True, related_name="variants")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offering", "sku"], condition=~Q(sku=""), name="unique_offering_variant_sku"),
            models.UniqueConstraint(fields=["offering", "combination_key"], condition=~Q(combination_key=""), name="unique_offering_variant_combination"),
        ]
        ordering = ["sort_order", "name"]


class OfferingMedia(models.Model):
    ROLE_CHOICES = [("cover", "Cover"), ("gallery", "Gallery"), ("hover", "Card hover"), ("model", "3D model"), ("poster", "3D poster")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="offering_media")
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="ordered_media")
    variant = models.ForeignKey(OfferingVariant, on_delete=models.CASCADE, blank=True, null=True, related_name="ordered_media")
    asset = models.ForeignKey(BusinessAsset, on_delete=models.PROTECT, related_name="offering_media")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="gallery")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offering", "asset", "variant", "role"], name="unique_offering_media_assignment", nulls_distinct=False),
            models.UniqueConstraint(fields=["offering", "role"], condition=Q(role__in=["cover", "hover", "model", "poster"]), name="unique_singleton_offering_media_role"),
        ]
        ordering = ["sort_order", "id"]


class OptionGroup(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="option_groups")
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="option_groups")
    name = models.CharField(max_length=120)
    minimum_choices = models.PositiveSmallIntegerField(default=0)
    maximum_choices = models.PositiveSmallIntegerField(default=1)
    is_required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [models.UniqueConstraint(fields=["offering", "name"], name="unique_offering_option_group")]


class OfferingOption(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="offering_options")
    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_delta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [models.UniqueConstraint(fields=["group", "name"], name="unique_group_offering_option")]


class OfferingFoodProfile(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="food_profiles")
    offering = models.OneToOneField(Offering, on_delete=models.CASCADE, related_name="food_profile")
    serving_label = models.CharField(max_length=100, blank=True)
    calories = models.PositiveIntegerField(blank=True, null=True)
    protein_grams = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    carbohydrate_grams = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    fat_grams = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    allergens = models.JSONField(default=list, blank=True)
    ingredients = models.TextField(blank=True, max_length=4000)


class OfferingCostComponent(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="offering_cost_components")
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="cost_components")
    name = models.CharField(max_length=160)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit = models.CharField(max_length=40, default="unit")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["name"]
