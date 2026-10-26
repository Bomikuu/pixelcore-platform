"""Published, image-backed demonstration content using existing CMS schemas."""

import hashlib
import json

from content.models import Site, SitePage
from content.services import create_revision, publish_revision
from displays.models import DisplayPublication
from displays.serializers import validate_display_settings


def publish_demo(ctx):
    site = ctx.save(Site, "site", business=ctx.business, name="Northline Demo Store",
        navigation=[{"label": "Shop", "path": "/shop"}, {"label": "Appointments", "path": "/services"}],
        settings={"template": "commerce", "announcement": "A fictional business with a month of sample activity."})
    page = ctx.save(SitePage, "page:home", site=site, title="Northline Supply Co.", slug="home",
                    page_type="home", no_index=True, seo_title="Northline | PixelCore monthly demonstration",
                    seo_description="Explore a fictional store populated with connected sample business activity.")
    content = {"schema_version": 1, "blocks": [
        {"id": "monthly-intro", "type": "promo_strip", "version": 1, "settings": {
            "message": "Sample store — all products and activity are fictional.", "label": "Explore the catalog", "path": "/shop"}},
        {"id": "monthly-hero", "type": "hero", "version": 1, "settings": {
            "eyebrow": "Northline Supply Co.", "heading": "Useful things for your everyday route.",
            "body": "Considered footwear, apparel, carry goods, and hands-on advice from our studio team.",
            "asset_id": str(ctx.assets["storefront-hero"].public_id), "primary_label": "Shop the collection",
            "primary_path": "/shop", "secondary_label": "Book a visit", "secondary_path": "/services", "alignment": "left"}},
        {"id": "monthly-products", "type": "product_rail", "version": 1, "settings": {
            "heading": "Everyday essentials", "offering_ids": [str(p.public_id) for p in ctx.products.values()], "limit": 6}},
        {"id": "monthly-studio", "type": "editorial_split", "version": 1, "settings": {
            "heading": "Meet us at the studio", "body": "Book personal shopping, wardrobe styling, or a practical product-care workshop.",
            "asset_id": str(ctx.assets["event-venue"].public_id), "label": "Explore appointments", "path": "/services", "media_side": "right"}},
        {"id": "monthly-services", "type": "service_grid", "version": 1, "settings": {"heading": "Appointments and workshops", "limit": 3, "layout": "grid"}},
        {"id": "monthly-contact", "type": "contact", "version": 1, "settings": {
            "heading": "Makati shop and studio", "body": "Fictional demonstration location.", "show_address": True, "show_phone": False, "show_email": True}},
    ]}
    checksum = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if page.published_revision is None or page.published_revision.checksum != checksum:
        publish_revision(page, create_revision(page, content, ctx.owner), ctx.owner)
    for key, name, kind, template in [
        ("catalog", "Northline essentials catalog", "catalog_board", "feature_rows"),
        ("studio", "Northline studio information", "information", "hero_list"),
    ]:
        settings = {"heading": name, "background": "#253029", "foreground": "#F6F1E8", "show_prices": True}
        validate_display_settings(settings)
        ctx.save(DisplayPublication, f"display:{key}", business=ctx.business, location=ctx.location,
            name=name, kind=kind, template=template, settings=settings,
            offering_ids=[str(p.public_id) for p in ctx.products.values()], background_asset=ctx.assets["storefront-hero"],
            is_active=True, is_published=True, created_by=ctx.owner, published_at=ctx.first)
