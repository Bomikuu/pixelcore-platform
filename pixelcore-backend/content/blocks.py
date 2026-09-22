import re

from rest_framework import serializers
from .hero import validate_hero_slides


BLOCK_SCHEMAS = {
    "hero": {"eyebrow", "heading", "body", "primary_label", "primary_path", "secondary_label", "secondary_path", "asset_id", "alignment"},
    "text": {"document", "width", "alignment"},
    "image": {"asset_id", "caption", "fit", "aspect_ratio"},
    "gallery": {"asset_ids", "columns", "captions"},
    "columns": {"columns", "gap"},
    "cta": {"heading", "body", "label", "path", "tone"},
    "faq": {"heading", "items"},
    "contact": {"heading", "body", "show_phone", "show_email", "show_address"},
    "product_grid": {"heading", "category_id", "limit", "layout"},
    "featured_products": {"heading", "offering_ids", "layout"},
    "service_grid": {"heading", "category_id", "limit", "layout"},
    "booking_cta": {"heading", "body", "service_id", "label"},
    "policy": {"heading", "document", "updated_label"},
    "three_hero": {"heading", "body", "asset_id", "poster_asset_id", "camera", "lighting", "background_color", "rotation", "motion"},
    "product_model": {"offering_id", "asset_id", "poster_asset_id", "camera", "lighting", "rotation", "motion"},
    "particle_scene": {"heading", "body", "poster_asset_id", "particle_count", "colors", "speed", "motion"},
    "commerce_hero": {"heading", "body", "offering_id", "offering_ids", "primary_label", "primary_path", "secondary_label", "secondary_path", "autoplay", "slides"},
    "product_rail": {"heading", "offering_ids", "limit"},
    "collection_feature": {"heading", "body", "collection_slug", "asset_id", "label", "path"},
    "category_tiles": {"heading", "items"},
    "editorial_split": {"heading", "body", "asset_id", "label", "path", "media_side"},
    "promo_strip": {"message", "label", "path"},
    "policy_highlights": {"items"},
}

MAX_BLOCKS = 60
MAX_DEPTH = 6
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
SAFE_PATH = re.compile(r"^/[A-Za-z0-9/_-]*$")
FORBIDDEN_KEYS = {"html", "raw_html", "javascript", "script", "shader", "css", "style", "url"}


def _walk(value, depth=0):
    if depth > MAX_DEPTH:
        raise serializers.ValidationError("Block settings are too deeply nested.")
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise serializers.ValidationError(f"'{key}' is not allowed in page content.")
            _walk(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 100:
            raise serializers.ValidationError("A block setting contains too many items.")
        for item in value:
            _walk(item, depth + 1)
    elif isinstance(value, str) and len(value) > 12000:
        raise serializers.ValidationError("A block text value is too long.")


def validate_page_content(value, business=None):
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise serializers.ValidationError("Page content must use schema_version 1.")
    blocks = value.get("blocks")
    if not isinstance(blocks, list) or len(blocks) > MAX_BLOCKS:
        raise serializers.ValidationError(f"Pages support up to {MAX_BLOCKS} blocks.")
    identifiers = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise serializers.ValidationError(f"Block {index + 1} must be an object.")
        block_id = str(block.get("id", ""))
        block_type = block.get("type")
        version = block.get("version")
        settings = block.get("settings")
        if not block_id or len(block_id) > 80 or block_id in identifiers:
            raise serializers.ValidationError(f"Block {index + 1} has an invalid or duplicate id.")
        identifiers.add(block_id)
        if block_type not in BLOCK_SCHEMAS or version != 1 or not isinstance(settings, dict):
            raise serializers.ValidationError(f"Block {block_id} has an unsupported type, version, or settings value.")
        unknown = set(settings) - BLOCK_SCHEMAS[block_type]
        if unknown:
            raise serializers.ValidationError(f"Block {block_id} has unsupported settings: {', '.join(sorted(unknown))}.")
        for key in ("path", "primary_path", "secondary_path"):
            if key in settings and settings[key] and not SAFE_PATH.fullmatch(str(settings[key])):
                raise serializers.ValidationError(f"Block {block_id} contains an unsafe internal path.")
        for key in ("background_color",):
            if key in settings and not HEX.fullmatch(str(settings[key])):
                raise serializers.ValidationError(f"Block {block_id} contains an invalid color.")
        if block_type == "particle_scene" and not 1 <= int(settings.get("particle_count", 300)) <= 1500:
            raise serializers.ValidationError("Particle scenes support between 1 and 1,500 particles.")
        if block_type in {"three_hero", "product_model", "particle_scene"}:
            if settings.get("motion", "subtle") not in {"none", "subtle", "interactive"}:
                raise serializers.ValidationError(f"Block {block_id} has an unsupported motion setting.")
            if float(settings.get("speed", 0.5)) > 1.5:
                raise serializers.ValidationError(f"Block {block_id} exceeds the motion speed limit.")
        if block_type == 'commerce_hero' and 'slides' in settings:
            settings['slides'] = validate_hero_slides(settings['slides'], business)
        _walk(settings)
    return value
