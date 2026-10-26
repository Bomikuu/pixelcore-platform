"""The demo tenant's catalog, media, people and suppliers."""

from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import CommandError
from django.utils import timezone

from businesses.models import AccountProfile, Business, BusinessAsset, BusinessLocation, BusinessMembership
from businesses.services import bootstrap_business
from catalog.models import Category, Offering, OfferingMedia, OfferingVariant, ProductCollection, ProductProfile, VariantDimension, VariantValue
from commerce.models import Customer, CustomerAddress, ShippingZone
from operations.models import InventoryBalance, Supplier, SupplierProduct
from scheduling.models import AvailabilityRule, ServiceAssignment, StaffProfile

from .common import DATASET, identity, money


def prepare_business(ctx, owner_email=None):
    User = get_user_model()
    expected = identity(ctx.slug, Business, "tenant")
    existing = Business.objects.filter(slug=ctx.slug).first()
    if existing and existing.public_id != expected:
        raise CommandError("That business slug already exists and is not managed by this demo fixture.")
    email = (owner_email or ("monthly.demo@example.test" if ctx.slug == ctx.data["business"]["slug"] else f"{ctx.slug}@example.test")).strip().lower()
    if owner_email:
        matches = User.objects.filter(email__iexact=email)
        if matches.count() != 1:
            raise CommandError("--owner-email must identify exactly one existing account.")
        owner = matches.get()
    else:
        username = f"{ctx.slug}-owner"
        owner = User.objects.filter(username=username).first()
        if owner is None:
            if User.objects.filter(email__iexact=email).exists():
                raise CommandError("The demo email already belongs to another account. Use --owner-email to attach an existing account.")
            owner = User.objects.create_user(username=username, email=email, password="PixelCoreDemo123!", first_name="Alex", last_name="Rivera")
            AccountProfile.objects.create(user=owner, email_verified_at=ctx.now)
        elif not existing or owner.pk != existing.created_by_id:
            raise CommandError("The demo username already belongs to another account.")
    if existing and existing.created_by_id != owner.pk:
        raise CommandError("This demo business belongs to a different owner. Reuse its original --owner-email.")
    ctx.owner = owner
    definition = ctx.data["business"]
    ctx.business, _ = Business.objects.get_or_create(slug=ctx.slug, defaults={
        **{k: definition[k] for k in ("display_name", "tagline", "description", "address", "city", "region", "postal_code", "country", "timezone", "currency")},
        "public_id": expected, "created_by": owner, "industry_preset": "hybrid", "status": "active",
        "industry": "Lifestyle retail and workshops", "contact_email": owner.email,
        "tax_status": "vat", "prices_include_tax": False,
        "branding": {"primary_color": "#253029", "secondary_color": "#17201C", "accent_color": "#D9F85D", "font_family": "Manrope", "border_radius": "medium"},
    })
    # Serialize repeat imports of the same tenant on PostgreSQL.
    ctx.business = Business.objects.select_for_update().get(pk=ctx.business.pk)
    BusinessMembership.objects.get_or_create(business=ctx.business, user=owner, defaults={"role": "owner", "status": "active"})
    bootstrap_business(ctx.business)
    ctx.business.capabilities.update(status="active")
    ctx.location = BusinessLocation.objects.get(business=ctx.business, code="main")
    if ctx.location.name == "Main location":
        ctx.location.name = "Makati shop and studio"
        ctx.location.save(update_fields=["name"])


def import_assets(ctx):
    for key, (row, payload, width, height, sha) in ctx.image_payloads.items():
        asset = ctx.save(BusinessAsset, f"asset:{key}", business=ctx.business,
                         title=f"Demo — {key.replace('-', ' ').title()}", alt_text=row["alt"],
                         asset_type="image", mime_type="image/png", size_bytes=len(payload),
                         uploaded_by=ctx.owner, processing_status="ready", validation_error="",
                         metadata={"demo_dataset": DATASET, "sha256": sha, "width": width, "height": height, "generated_by": "image_gen"})
        filename = f"demo/monthly/{ctx.business.public_id}/{key}-{sha[:12]}.png"
        storage = asset.file.storage
        if not storage.exists(filename):
            filename = storage.save(filename, ContentFile(payload))
            ctx.new_files.append((storage, filename))
        if asset.file.name != filename:
            asset.file.name = filename
            asset.save(update_fields=["file"])
        ctx.assets[key] = asset
    if ctx.business.cover_image.name != ctx.assets["storefront-hero"].file.name:
        ctx.business.cover_image.name = ctx.assets["storefront-hero"].file.name
        ctx.business.save(update_fields=["cover_image"])


def import_catalog(ctx):
    categories = {}
    for index, row in enumerate(ctx.data["products"]):
        name = row["category"]
        if name not in categories:
            categories[name] = ctx.save(Category, f"category:{name}", business=ctx.business, name=name,
                                        slug=name.lower().replace(" ", "-"), sort_order=len(categories),
                                        cover_asset=ctx.assets[row["image"]], is_active=True)
        product = ctx.save(Offering, f"product:{row['id']}", business=ctx.business, category=categories[name],
                           name=row["name"], slug=row["id"], summary=row["summary"], description=row["summary"],
                           offering_type="physical", status="published", fulfillment_type="delivery",
                           base_price=money(row["price"]), tax_rate=Decimal("12.000"),
                           sku=f"DEMO-{index + 1:03}", track_inventory=True,
                           metadata={"demo_dataset": DATASET, "badge": "New arrivals" if index < 2 else "Everyday essential"})
        product.assets.set([ctx.assets[row["image"]]])
        ctx.save(OfferingMedia, f"cover:{row['id']}", business=ctx.business, offering=product,
                 asset=ctx.assets[row["image"]], variant=None, role="cover", sort_order=0)
        ctx.save(ProductProfile, f"profile:{row['id']}", business=ctx.business, offering=product,
                 brand="Northline", tags=["demo", "everyday", name.lower()],
                 storefront_highlighted=index == 0, card_gallery_enabled=False,
                 materials="Knit textile and natural rubber" if index == 0 else "See product specifications",
                 care_instructions="Clean gently and air dry. Follow the material care label.",
                 specifications={"Collection": "Northline everyday essentials", "Demo": "Fictional product"})
        ctx.products[row["id"]] = product
        dimension_name = "Size" if name in {"Footwear", "Apparel"} else "Capacity" if row["id"] == "signal-bottle" else "Color"
        dimension = ctx.save(VariantDimension, f"dimension:{row['id']}", business=ctx.business,
                             offering=product, name=dimension_name, display_type="text", sort_order=0)
        for definition in row["variants"]:
            key = f"{row['id']}:{definition['id']}"
            value = ctx.save(VariantValue, f"value:{key}", business=ctx.business, dimension=dimension,
                             label=definition["name"].split(" / ")[-1], sort_order=len(ctx.variants))
            variant = ctx.save(OfferingVariant, f"variant:{key}", offering=product,
                               name=definition["name"], sku=definition["sku"], price=money(row["price"]),
                               unit_cost=money(row["cost"]), attributes={dimension_name: value.label},
                               combination_key=str(value.public_id), is_active=True)
            variant.option_values.set([value])
            ctx.variants[key], ctx.costs[key] = variant, money(row["cost"])
            balance = ctx.save(InventoryBalance, f"balance:{key}", business=ctx.business, variant=variant,
                               location=ctx.location, low_stock_threshold=5, reorder_quantity=24,
                               target_stock_level=60, bin_location=f"DEMO-A{index + 1}",
                               notes="Reconciled from fixture stock movements.")
            ctx.balances[key] = balance
    for key, name, products in [("new-arrivals", "New Arrivals", list(ctx.products.values())[:3]),
                                 ("daily-essentials", "Daily Essentials", list(ctx.products.values())[2:])]:
        collection = ctx.save(ProductCollection, f"collection:{key}", business=ctx.business, name=name,
                              slug=key, is_published=True, cover_asset=ctx.assets["storefront-hero"])
        collection.offerings.set(products)
    service_category = ctx.save(Category, "category:services", business=ctx.business, name="Appointments and workshops", slug="services", show_in_header=False)
    for row in ctx.data["services"]:
        service = ctx.save(Offering, f"service:{row['id']}", business=ctx.business,
            category=service_category, name=row["name"], slug=row["id"], summary=row["summary"], description=row["summary"],
            offering_type="service", status="published", base_price=money(row["price"]),
            duration_minutes=row["duration_minutes"], capacity=1, tax_rate=Decimal("12.000"), metadata={"demo_dataset": DATASET})
        image = ctx.assets["event-venue" if row["id"] == "product-care-workshop" else "storefront-hero"]
        service.assets.set([image])
        ctx.save(OfferingMedia, f"service-cover:{row['id']}", business=ctx.business, offering=service,
                 asset=image, role="cover", variant=None, sort_order=0)
        ctx.services[row["id"]] = service
    ctx.save(ShippingZone, "shipping:metro-manila", business=ctx.business, name="Metro Manila delivery",
             regions=["Metro Manila"], flat_rate=money("120"), is_active=True)


def import_people(ctx):
    for row in ctx.data["customers"]:
        customer = ctx.save(Customer, row["id"], business=ctx.business,
                            **{k: row[k] for k in ("first_name", "last_name", "email", "phone")},
                            notes="Fictional sample customer. Do not contact.")
        ctx.customers[row["id"]] = customer
        ctx.save(CustomerAddress, f"address:{row['id']}", customer=customer, label="Home",
                 recipient_name=f"{row['first_name']} {row['last_name']}", phone=row["phone"],
                 line1="12 Sample Street", city=row["city"], region="Metro Manila", postal_code="1200", country="PH", is_default=True)
    User = get_user_model()
    for index, row in enumerate(ctx.data["staff"]):
        username = f"{ctx.slug}-{row['id']}"
        user = User.objects.filter(username=username).first()
        if user and not BusinessMembership.objects.filter(user=user, business=ctx.business).exists():
            raise CommandError("A demo staff username belongs to another account.")
        if user is None:
            staff_email = f"{ctx.slug}.{row['id']}@example.test"
            if User.objects.filter(email__iexact=staff_email).exists():
                raise CommandError("A sample staff email is already in use by another account.")
            first, _, last = row["name"].partition(" ")
            user = User.objects.create_user(username=username, email=staff_email, first_name=first, last_name=last)
        membership, _ = BusinessMembership.objects.get_or_create(user=user, business=ctx.business,
            defaults={"role": "manager" if index == 0 else "staff", "status": "active"})
        profile = ctx.save(StaffProfile, row["id"], business=ctx.business, membership=membership,
                           display_name=row["name"], email=row["email"], job_title=row["job_title"],
                           hired_at=(ctx.first - timedelta(days=120)).date(), scheduled_start_time=time(9),
                           scheduled_end_time=time(18), is_bookable=row["is_bookable"], is_active=True,
                           bio="Fictional team member for the monthly demonstration.", timezone="Asia/Manila")
        ctx.staff[row["id"]] = profile
        if row["is_bookable"]:
            for weekday in range(6):
                ctx.save(AvailabilityRule, f"availability:{row['id']}:{weekday}", business=ctx.business,
                         staff=profile, location=ctx.location, weekday=weekday, starts_at=time(9), ends_at=time(18), is_active=True)
            for key, service in ctx.services.items():
                ctx.save(ServiceAssignment, f"assignment:{row['id']}:{key}", business=ctx.business,
                         staff=profile, offering=service, location=ctx.location, is_active=True)
    for row in ctx.data["suppliers"]:
        supplier = ctx.save(Supplier, row["id"], business=ctx.business, name=row["name"],
            category=row["category"], contact_name=row["contact_name"], email=row["email"],
            code=f"DEMO-{row['id'].upper()}", payment_terms_days=15, lead_time_days=4,
            image=ctx.assets[row["image"]], notes="Fictional demo supplier. No messages are sent.")
        ctx.suppliers[row["id"]] = supplier
    suppliers = list(ctx.suppliers.values())
    for index, (key, variant) in enumerate(ctx.variants.items()):
        supplier = suppliers[index % len(suppliers)]
        ctx.save(SupplierProduct, f"source:{key}", business=ctx.business, supplier=supplier,
                 variant=variant, supplier_sku=f"SRC-{variant.sku}", last_unit_cost=ctx.costs[key], minimum_order_quantity=12, lead_time_days=4)
        InventoryBalance.objects.filter(pk=ctx.balances[key].pk).update(preferred_supplier=supplier)
