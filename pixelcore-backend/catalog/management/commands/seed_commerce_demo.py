import hashlib
import io
import json
import math
import struct
from decimal import Decimal
from itertools import product as cartesian_product

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from businesses.models import AccountProfile, Business, BusinessAsset, BusinessMembership
from businesses.services import bootstrap_business, set_capabilities
from catalog.glb import validate_glb
from catalog.models import (
    Category,
    Offering,
    OfferingMedia,
    OfferingVariant,
    ProductCollection,
    ProductProfile,
    VariantDimension,
    VariantValue,
)
from commerce.models import Discount, ShippingZone
from content.models import Site, SitePage
from content.services import create_revision, publish_revision
from operations.models import InventoryBalance


DEMO_PRODUCTS = [
    {
        "name": "Transit Runner",
        "slug": "transit-runner",
        "category": "Footwear",
        "collections": ["New Arrivals", "Trail Series"],
        "summary": "A lightweight everyday trainer shaped for city miles and weekend detours.",
        "description": "Breathable engineered knit, a stable heel cradle, and a softly responsive sole make the Transit Runner an easy all-day choice.",
        "price": "5890.00",
        "compare_at": "6490.00",
        "cost": "2380.00",
        "sku": "NL-TR",
        "dimensions": [
            ("Size", "text", [("7", ""), ("8", ""), ("9", ""), ("10", "")]),
            ("Color", "color", [("Stone", "#D6D0C4"), ("Moss", "#65735A")]),
        ],
        "palette": ("#D6D0C4", "#1E302A", "#E1FF70"),
        "materials": "Engineered knit upper, recycled textile lining, rubber outsole.",
        "care": "Spot clean with a soft brush and mild soap. Air dry away from direct heat.",
        "weight": 780,
        "dimensions_cm": {"length": 34, "width": 22, "height": 13},
        "specifications": {"Fit": "True to size", "Cushioning": "Responsive", "Use": "Everyday movement"},
        "size_guide": {"unit": "cm", "rows": [{"label": "7", "foot_length": 25}, {"label": "8", "foot_length": 26}, {"label": "9", "foot_length": 27}, {"label": "10", "foot_length": 28}]},
        "model": True,
    },
    {
        "name": "Ridge Utility Jacket",
        "slug": "ridge-utility-jacket",
        "category": "Apparel",
        "collections": ["New Arrivals", "Trail Series"],
        "summary": "A weather-ready layer with clean storage and an adaptable silhouette.",
        "description": "The Ridge jacket balances a structured outer shell with a light mesh lining, adjustable cuffs, and secure everyday pockets.",
        "price": "4290.00",
        "compare_at": None,
        "cost": "1720.00",
        "sku": "NL-RJ",
        "dimensions": [
            ("Size", "text", [("S", ""), ("M", ""), ("L", ""), ("XL", "")]),
            ("Color", "color", [("Ink", "#1B252C"), ("Clay", "#A9684D")]),
        ],
        "palette": ("#A9684D", "#182229", "#F6F1E8"),
        "materials": "Water-resistant cotton-nylon shell with recycled mesh lining.",
        "care": "Machine wash cold on a gentle cycle. Close fasteners before washing and line dry.",
        "weight": 620,
        "dimensions_cm": {"length": 40, "width": 30, "height": 8},
        "specifications": {"Fit": "Relaxed", "Pockets": "Four", "Weather": "Light rain"},
        "size_guide": {"unit": "cm", "rows": [{"label": "S", "chest": 96}, {"label": "M", "chest": 102}, {"label": "L", "chest": 108}, {"label": "XL", "chest": 116}]},
    },
    {
        "name": "Atlas Everyday Tee",
        "slug": "atlas-everyday-tee",
        "category": "Apparel",
        "collections": ["Daily Essentials"],
        "summary": "A substantial everyday tee cut with room to move.",
        "description": "Made from combed cotton with a softly structured collar, the Atlas Tee is designed to hold its shape through repeat wear.",
        "price": "1490.00",
        "compare_at": "1790.00",
        "cost": "520.00",
        "sku": "NL-AT",
        "dimensions": [
            ("Size", "text", [("S", ""), ("M", ""), ("L", ""), ("XL", "")]),
            ("Color", "color", [("Chalk", "#EEEADF"), ("Signal", "#D9F85D")]),
        ],
        "palette": ("#D9F85D", "#253029", "#EEEADF"),
        "materials": "240 gsm combed cotton jersey.",
        "care": "Wash inside out in cold water. Line dry and use a cool iron.",
        "weight": 280,
        "dimensions_cm": {"length": 31, "width": 24, "height": 4},
        "specifications": {"Fit": "Relaxed", "Fabric": "240 gsm", "Neckline": "Ribbed crew"},
        "size_guide": {"unit": "cm", "rows": [{"label": "S", "chest": 96}, {"label": "M", "chest": 102}, {"label": "L", "chest": 108}, {"label": "XL", "chest": 116}]},
    },
    {
        "name": "Field Day Tote",
        "slug": "field-day-tote",
        "category": "Everyday Carry",
        "collections": ["Daily Essentials"],
        "summary": "An organized carry-all for commutes, markets, and short trips.",
        "description": "A wide-opening tote with a reinforced base, laptop sleeve, bottle pocket, and adjustable shoulder strap.",
        "price": "2690.00",
        "compare_at": None,
        "cost": "980.00",
        "sku": "NL-FT",
        "dimensions": [("Color", "color", [("Sand", "#C7AA7B"), ("Night", "#20262B")])],
        "palette": ("#C7AA7B", "#20262B", "#F2E6CE"),
        "materials": "Heavyweight recycled canvas with nylon lining.",
        "care": "Wipe clean with a damp cloth. Do not machine wash.",
        "weight": 540,
        "dimensions_cm": {"length": 42, "width": 16, "height": 34},
        "specifications": {"Capacity": "22 L", "Laptop sleeve": "Up to 15 inches", "Closure": "Zip"},
        "size_guide": {},
    },
    {
        "name": "Signal Bottle",
        "slug": "signal-bottle",
        "category": "Everyday Carry",
        "collections": ["New Arrivals", "Daily Essentials"],
        "summary": "A double-wall bottle with a tactile powder-coated finish.",
        "description": "Keeps everyday drinks at temperature with a leak-resistant cap and an easy-carry loop.",
        "price": "1290.00",
        "compare_at": None,
        "cost": "430.00",
        "sku": "NL-SB",
        "dimensions": [
            ("Capacity", "text", [("600 ml", ""), ("900 ml", "")]),
            ("Color", "color", [("Cobalt", "#2459D3"), ("Lime", "#D9F85D")]),
        ],
        "palette": ("#2459D3", "#D9F85D", "#F1F5F9"),
        "materials": "Food-grade stainless steel with a BPA-free polypropylene cap.",
        "care": "Hand wash recommended. Do not place in a microwave or freezer.",
        "weight": 410,
        "dimensions_cm": {"length": 9, "width": 9, "height": 28},
        "specifications": {"Insulation": "Double wall", "Seal": "Leak resistant", "Finish": "Powder coat"},
        "size_guide": {},
    },
    {
        "name": "Relay Crossbody",
        "slug": "relay-crossbody",
        "category": "Everyday Carry",
        "collections": ["Trail Series"],
        "summary": "A compact crossbody that keeps daily essentials close and ordered.",
        "description": "Three accessible compartments, a soft-lined device pocket, and an adjustable strap in a low-profile form.",
        "price": "1890.00",
        "compare_at": "2190.00",
        "cost": "710.00",
        "sku": "NL-RC",
        "dimensions": [("Color", "color", [("Graphite", "#3B4145"), ("Olive", "#6F7352")])],
        "palette": ("#6F7352", "#272C2F", "#E4DDBD"),
        "materials": "Recycled ripstop shell with polyester lining.",
        "care": "Spot clean and air dry.",
        "weight": 290,
        "dimensions_cm": {"length": 25, "width": 8, "height": 18},
        "specifications": {"Capacity": "4 L", "Compartments": "Three", "Strap": "Adjustable"},
        "size_guide": {},
    },
]


class NamedBytesIO(io.BytesIO):
    def __init__(self, value, name):
        super().__init__(value)
        self.name = name
        self.size = len(value)


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _product_art(product, alternate=False):
    width, height = 1200, 1500
    primary, dark, accent = product["palette"]
    background = dark if alternate else primary
    foreground = primary if alternate else dark
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 70, 1130, 1430), radius=42, outline=accent, width=4)
    draw.text((100, 105), "NORTHLINE / FIELD NOTES", fill=accent, font=_font(25, True))
    draw.text((100, 170), product["name"].upper(), fill=foreground, font=_font(64, True))
    draw.text((102, 255), product["summary"], fill=foreground, font=_font(28), spacing=10)

    center_x, center_y = 600, 820
    if "Runner" in product["name"]:
        points = [(255, 855), (405, 710), (710, 725), (835, 805), (1000, 870), (920, 1015), (375, 1015), (230, 940)]
        draw.polygon(points, fill=accent, outline=foreground, width=12)
        draw.line((330, 940, 930, 940), fill=foreground, width=22)
        draw.ellipse((745, 790, 870, 915), outline=foreground, width=10)
    elif "Jacket" in product["name"] or "Tee" in product["name"]:
        points = [(420, 590), (310, 720), (380, 805), (435, 750), (435, 1120), (765, 1120), (765, 750), (820, 805), (890, 720), (780, 590), (680, 550), (520, 550)]
        draw.polygon(points, fill=accent, outline=foreground, width=12)
        draw.line((600, 575, 600, 1110), fill=foreground, width=8)
    elif "Bottle" in product["name"]:
        draw.rounded_rectangle((455, 500, 745, 1130), radius=95, fill=accent, outline=foreground, width=12)
        draw.rounded_rectangle((515, 425, 685, 555), radius=35, fill=accent, outline=foreground, width=12)
        draw.arc((505, 620, 695, 820), 210, 510, fill=foreground, width=10)
    else:
        draw.rounded_rectangle((315, 560, 885, 1080), radius=70, fill=accent, outline=foreground, width=12)
        draw.arc((430, 420, 770, 720), 185, 355, fill=foreground, width=18)
        draw.line((600, 565, 600, 1080), fill=foreground, width=7)

    draw.text((100, 1305), "DESIGNED FOR THE EVERYDAY ROUTE", fill=foreground, font=_font(27, True))
    draw.text((100, 1355), f"PHP {Decimal(product['price']):,.2f}", fill=accent, font=_font(30, True))
    output = io.BytesIO()
    image.save(output, format="WEBP", quality=90, method=6)
    return output.getvalue()


def _demo_glb():
    positions = [
        (-1.35, -0.35, -0.55), (1.35, -0.35, -0.55), (1.35, 0.35, -0.55), (-1.35, 0.35, -0.55),
        (-1.35, -0.35, 0.55), (1.35, -0.35, 0.55), (1.35, 0.35, 0.55), (-1.35, 0.35, 0.55),
    ]
    indices = [0, 1, 2, 0, 2, 3, 4, 6, 5, 4, 7, 6, 0, 4, 5, 0, 5, 1, 1, 5, 6, 1, 6, 2, 2, 6, 7, 2, 7, 3, 3, 7, 4, 3, 4, 0]
    position_bytes = b"".join(struct.pack("<fff", *position) for position in positions)
    index_bytes = b"".join(struct.pack("<H", index) for index in indices)
    binary = position_bytes + index_bytes
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    document = {
        "asset": {"version": "2.0", "generator": "PixelCore commerce demo"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "rotation": [0.0, 0.0, math.sin(-0.08), math.cos(-0.08)]}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0, "mode": 4}]}],
        "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [0.85, 0.97, 0.36, 1.0], "metallicFactor": 0.05, "roughnessFactor": 0.65}, "doubleSided": True}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(position_bytes), "target": 34962}, {"buffer": 0, "byteOffset": len(position_bytes), "byteLength": len(index_bytes), "target": 34963}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3", "min": [-1.35, -0.35, -0.55], "max": [1.35, 0.35, 0.55]}, {"bufferView": 1, "componentType": 5123, "count": len(indices), "type": "SCALAR"}],
    }
    json_bytes = json.dumps(document, separators=(",", ":")).encode()
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary)
    return b"glTF" + struct.pack("<II", 2, total_length) + struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes + struct.pack("<II", len(binary), 0x004E4942) + binary


class Command(BaseCommand):
    help = "Create or refresh the local Northline commerce demonstration tenant."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@pixelcore.local")
        parser.add_argument("--password", default="PixelCoreDemo123!")
        parser.add_argument("--slug", default="northline-demo")
        parser.add_argument("--allow-production", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError("This demonstration seed is disabled outside DEBUG. Pass --allow-production only for an intentional non-production demo environment.")

        with transaction.atomic():
            user = self._upsert_user(options["email"], options["password"])
            business = self._upsert_business(user, options["slug"])
            bootstrap_business(business)
            set_capabilities(business, ["site", "sell", "schedule", "operate"], user)
            location = business.locations.filter(is_primary=True).first() or business.locations.first()
            products, assets = self._upsert_catalog(business, user, location)
            self._upsert_commerce(business)
            self._upsert_site(business, user, products, assets)

        self.stdout.write(self.style.SUCCESS("Northline commerce demonstration is ready."))
        self.stdout.write(f"Storefront: http://localhost/site/{business.slug}")
        self.stdout.write(f"Shop:       http://localhost/site/{business.slug}/shop")
        self.stdout.write("Workspace:  http://localhost/login")
        self.stdout.write(f"Email:      {user.email}")
        self.stdout.write(f"Password:   {options['password']}")
        self.stdout.write("Promo code: WELCOME10")

    def _upsert_user(self, email, password):
        User = get_user_model()
        normalized = User.objects.normalize_email(email).lower()
        user, _ = User.objects.get_or_create(
            email=normalized,
            defaults={"username": "northline_owner", "first_name": "Alex", "last_name": "Rivera"},
        )
        user.username = user.username or "northline_owner"
        user.first_name = "Alex"
        user.last_name = "Rivera"
        user.is_active = True
        user.set_password(password)
        user.save()
        profile, _ = AccountProfile.objects.get_or_create(user=user)
        if not profile.email_verified_at:
            profile.email_verified_at = timezone.now()
            profile.save(update_fields=["email_verified_at", "updated_at"])
        return user

    def _upsert_business(self, user, slug):
        business, _ = Business.objects.update_or_create(
            slug=slug,
            defaults={
                "created_by": user,
                "display_name": "Northline Supply Co.",
                "legal_name": "Northline Supply Company",
                "industry_preset": "retail",
                "industry": "Lifestyle retail",
                "tagline": "Useful things for the everyday route.",
                "description": "Northline is a fictional PixelCore demonstration store for apparel, footwear, and practical everyday carry.",
                "status": "active",
                "contact_email": user.email,
                "contact_phone": "+63 917 555 0142",
                "address": "32 Demo Avenue",
                "city": "Makati",
                "region": "Metro Manila",
                "postal_code": "1200",
                "country": "PH",
                "timezone": "Asia/Manila",
                "locale": "en-PH",
                "currency": "PHP",
                "branding": {"primary_color": "#253029", "secondary_color": "#17201C", "accent_color": "#D9F85D", "font_family": "Manrope", "border_radius": "medium"},
            },
        )
        BusinessMembership.objects.update_or_create(business=business, user=user, defaults={"role": "owner", "status": "active"})
        return business

    def _upsert_asset(self, business, user, title, filename, payload, mime_type, asset_type="image", metadata=None):
        asset = BusinessAsset.objects.filter(business=business, title=title).first()
        is_new = asset is None
        if asset is None:
            asset = BusinessAsset(business=business, title=title, uploaded_by=user)
        asset.alt_text = title
        asset.asset_type = asset_type
        asset.mime_type = mime_type
        asset.size_bytes = len(payload)
        asset.metadata = metadata or {}
        asset.processing_status = "ready"
        asset.validation_error = ""
        if is_new or not asset.file:
            asset.file.save(filename, ContentFile(payload), save=False)
        asset.save()
        return asset

    def _upsert_catalog(self, business, user, location):
        categories = {}
        for index, name in enumerate(["Footwear", "Apparel", "Everyday Carry"]):
            category, _ = Category.objects.update_or_create(business=business, slug=name.lower().replace(" ", "-"), defaults={"name": name, "description": f"Northline {name.lower()} for daily use.", "sort_order": index, "header_order": index, "show_in_header": True, "is_active": True})
            categories[name] = category

        collections = {}
        collection_copy = {
            "New Arrivals": "Recent additions with clear purpose and considered details.",
            "Daily Essentials": "Reliable pieces designed for repeat use.",
            "Trail Series": "Adaptable equipment for longer routes and changing conditions.",
        }
        for index, (name, description) in enumerate(collection_copy.items()):
            collection, _ = ProductCollection.objects.update_or_create(
                business=business,
                slug=name.lower().replace(" ", "-"),
                defaults={"name": name, "description": description, "sort_order": index, "is_published": True},
            )
            collections[name] = collection

        seeded_products = []
        seeded_assets = {}
        ProductProfile.objects.filter(business=business, storefront_highlighted=True).update(storefront_highlighted=False)
        for product_index, definition in enumerate(DEMO_PRODUCTS):
            offering, _ = Offering.objects.update_or_create(
                business=business,
                slug=definition["slug"],
                defaults={
                    "category": categories[definition["category"]],
                    "name": definition["name"],
                    "summary": definition["summary"],
                    "description": definition["description"],
                    "offering_type": "physical",
                    "status": "published",
                    "fulfillment_type": "delivery",
                    "base_price": Decimal(definition["price"]),
                    "compare_at_price": Decimal(definition["compare_at"]) if definition["compare_at"] else None,
                    "tax_rate": Decimal("12.000"),
                    "sku": definition["sku"],
                    "track_inventory": True,
                    "metadata": {"badge": "New" if "New Arrivals" in definition["collections"] else "Core"},
                },
            )
            ProductProfile.objects.update_or_create(
                offering=offering,
                defaults={
                    "business": business,
                    "brand": "Northline",
                    "tags": ["everyday", "northline", definition["category"].lower().replace(" ", "-")],
                    "materials": definition["materials"],
                    "care_instructions": definition["care"],
                    "shipping_weight_grams": definition["weight"],
                    "shipping_dimensions": definition["dimensions_cm"],
                    "size_guide": definition["size_guide"],
                    "specifications": definition["specifications"],
                    "seo_title": f"{definition['name']} | Northline",
                    "seo_description": definition["summary"],
                    "card_hover_enabled": True,
                    "card_gallery_enabled": product_index < 3,
                    "storefront_highlighted": product_index == 0,
                },
            )

            cover = self._upsert_asset(business, user, f"{definition['name']} — cover", f"{definition['slug']}-cover.webp", _product_art(definition), "image/webp", metadata={"width": 1200, "height": 1500, "demo": True})
            gallery = self._upsert_asset(business, user, f"{definition['name']} — alternate", f"{definition['slug']}-alternate.webp", _product_art(definition, alternate=True), "image/webp", metadata={"width": 1200, "height": 1500, "demo": True})
            offering.assets.set([cover, gallery])
            OfferingMedia.objects.update_or_create(offering=offering, role="cover", defaults={"business": business, "asset": cover, "variant": None, "sort_order": 0})
            OfferingMedia.objects.update_or_create(offering=offering, asset=gallery, variant=None, role="gallery", defaults={"business": business, "sort_order": 1})
            OfferingMedia.objects.update_or_create(offering=offering, role="hover", defaults={"business": business, "asset": gallery, "variant": None, "sort_order": 1})
            category = categories[definition["category"]]
            if not category.cover_asset_id:
                category.cover_asset = cover
                category.save(update_fields=["cover_asset", "updated_at"])
            seeded_assets[definition["slug"]] = cover

            dimensions = []
            for dimension_index, (name, display_type, values) in enumerate(definition["dimensions"]):
                dimension, _ = VariantDimension.objects.update_or_create(offering=offering, name=name, defaults={"business": business, "display_type": display_type, "sort_order": dimension_index})
                value_records = []
                for value_index, (label, swatch) in enumerate(values):
                    value, _ = VariantValue.objects.update_or_create(dimension=dimension, label=label, defaults={"business": business, "swatch_color": swatch, "sort_order": value_index})
                    value_records.append(value)
                dimensions.append(value_records)

            expected_keys = []
            for variant_index, combination in enumerate(cartesian_product(*dimensions)):
                combination_key = "|".join(str(value.public_id) for value in combination)
                expected_keys.append(combination_key)
                labels = [value.label for value in combination]
                variant, _ = OfferingVariant.objects.update_or_create(
                    offering=offering,
                    combination_key=combination_key,
                    defaults={
                        "name": " / ".join(labels),
                        "sku": f"{definition['sku']}-{'-'.join(label.upper().replace(' ', '') for label in labels)}",
                        "barcode": f"88{product_index + 1:02d}{variant_index + 1:06d}",
                        "price": Decimal(definition["price"]),
                        "compare_at_price": Decimal(definition["compare_at"]) if definition["compare_at"] else None,
                        "unit_cost": Decimal(definition["cost"]),
                        "attributes": {value.dimension.name: value.label for value in combination},
                        "is_active": True,
                        "sort_order": variant_index,
                    },
                )
                variant.option_values.set(combination)
                InventoryBalance.objects.update_or_create(
                    business=business,
                    variant=variant,
                    location=location,
                    defaults={"on_hand": Decimal(12 + ((product_index + variant_index) % 15)), "reserved": Decimal("0"), "low_stock_threshold": Decimal("4")},
                )
            OfferingVariant.objects.filter(offering=offering).exclude(combination_key__in=expected_keys).update(is_active=False)

            for collection_name in definition["collections"]:
                collections[collection_name].offerings.add(offering)
            seeded_products.append(offering)

        lead = seeded_products[0]
        glb = _demo_glb()
        upload = NamedBytesIO(glb, "transit-runner.glb")
        model_metadata, validation_error = validate_glb(upload)
        if validation_error:
            raise CommandError(f"Generated demo model was rejected: {validation_error}")
        model_asset = self._upsert_asset(business, user, "Transit Runner — 3D model", "transit-runner.glb", glb, "model/gltf-binary", "model", model_metadata)
        OfferingMedia.objects.update_or_create(offering=lead, role="model", defaults={"business": business, "asset": model_asset, "variant": None, "sort_order": 2})
        OfferingMedia.objects.update_or_create(offering=lead, role="poster", defaults={"business": business, "asset": seeded_assets[lead.slug], "variant": None, "sort_order": 3})
        lead.assets.add(model_asset)

        for collection in collections.values():
            hero_offerings = list(collection.offerings.order_by("name")[:5])
            first_offering = hero_offerings[0] if hero_offerings else None
            if first_offering:
                collection.cover_asset = seeded_assets[first_offering.slug]
                collection.hero_settings = {
                    "enabled": True,
                    "heading": collection.name,
                    "body": collection.description,
                    "offering_ids": [str(offering.public_id) for offering in hero_offerings],
                    "autoplay": True,
                }
                collection.save(update_fields=["cover_asset", "hero_settings", "updated_at"])
        return seeded_products, seeded_assets

    def _upsert_commerce(self, business):
        ShippingZone.objects.update_or_create(business=business, name="Metro Manila", defaults={"regions": ["Metro Manila", "NCR"], "flat_rate": Decimal("120.00"), "is_active": True})
        ShippingZone.objects.update_or_create(business=business, name="Rest of the Philippines", defaults={"regions": ["Philippines"], "flat_rate": Decimal("220.00"), "is_active": True})
        Discount.objects.update_or_create(
            business=business,
            code="WELCOME10",
            defaults={"name": "Welcome 10%", "value_type": "percentage", "value": Decimal("10.00"), "is_automatic": False, "is_active": True, "offering_ids": []},
        )

    def _upsert_site(self, business, user, products, assets):
        site, _ = Site.objects.update_or_create(
            business=business,
            defaults={
                "name": "Northline Store",
                "navigation": [
                    {"label": "Shop", "path": "/shop"},
                    {"label": "New arrivals", "path": "/collection/new-arrivals"},
                    {"label": "Wishlist", "path": "/wishlist"},
                ],
                "settings": {"template": "commerce", "announcement": "Free pickup from our Makati demo location."},
            },
        )
        page, _ = SitePage.objects.update_or_create(
            site=site,
            slug="home",
            defaults={
                "title": "Northline Supply Co.",
                "page_type": "home",
                "seo_title": "Northline Supply Co. | Everyday equipment",
                "seo_description": "Explore Northline footwear, apparel, and everyday carry in this PixelCore demonstration storefront.",
                "no_index": True,
            },
        )
        lead = products[0]
        content = {
            "schema_version": 1,
            "blocks": [
                {"id": "northline-promo", "type": "promo_strip", "version": 1, "settings": {"message": "Welcome to the PixelCore commerce demo", "label": "Shop the collection", "path": "/shop"}},
                {"id": "northline-hero", "type": "commerce_hero", "version": 1, "settings": {"heading": "Built for the everyday route.", "body": "A considered edit of adaptable footwear, apparel, and carry goods.", "offering_id": str(lead.public_id), "offering_ids": [str(item.public_id) for item in products[:3]], "primary_label": "Shop new arrivals", "primary_path": "/collection/new-arrivals", "secondary_label": "Explore all products", "secondary_path": "/shop", "autoplay": True}},
                {"id": "northline-new", "type": "product_rail", "version": 1, "settings": {"heading": "New arrivals", "offering_ids": [str(item.public_id) for item in products[:4]], "limit": 4}},
                {"id": "northline-field", "type": "collection_feature", "version": 1, "settings": {"heading": "Go farther with less.", "body": "The Trail Series puts adaptable layers and compact carry at the center of the route.", "collection_slug": "trail-series", "asset_id": str(assets["ridge-utility-jacket"].public_id), "label": "Explore Trail Series", "path": "/collection/trail-series"}},
                {"id": "northline-values", "type": "policy_highlights", "version": 1, "settings": {"items": [{"heading": "Secure checkout", "body": "Server-priced carts and protected order access."}, {"heading": "Flexible fulfillment", "body": "Delivery or pickup based on your business settings."}, {"heading": "Purposeful details", "body": "Materials, care, fit, and specifications where they matter."}]}},
            ],
        }
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(canonical.encode()).hexdigest()
        if not page.published_revision or page.published_revision.checksum != checksum:
            revision = create_revision(page, content, user)
            publish_revision(page, revision, user)
        elif site.status != "published":
            site.status = "published"
            site.published_at = timezone.now()
            site.save(update_fields=["status", "published_at", "updated_at"])
