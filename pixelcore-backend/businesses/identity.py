import copy
import html
import re
import uuid
from html.parser import HTMLParser
from urllib.parse import urlparse

from rest_framework import serializers


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
CLASS_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
PLATFORM_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
ALLOWED_FONTS = {
    "Manrope",
    "Newsreader",
    "Plus Jakarta Sans",
    "Inter",
    "Poppins",
    "Montserrat",
    "Playfair Display",
    "system-ui",
}
ALLOWED_RADII = {"none", "small", "medium", "large", "pill"}
RADIUS_VALUES = {"none": "0px", "small": "4px", "medium": "8px", "large": "12px", "pill": "999px"}


def default_identity_config():
    return {
        "schema_version": 1,
        "primary_color": "#165B4C",
        "secondary_color": "#17362F",
        "accent_color": "#D8922B",
        "background_color": "#FAF9F5",
        "text_color": "#17312B",
        "muted_text_color": "#5D6D68",
        "link_color": "#165B4C",
        "font_family": "Manrope",
        "heading_font_family": "Newsreader",
        "border_radius": "medium",
        "typography": {
            "primary_font": "Manrope",
            "heading_font": "Newsreader",
            "body_weight": 400,
            "heading_weight": 700,
            "base_font_size": "16px",
        },
        "style": {
            "button_radius": "medium",
            "card_radius": "large",
            "input_radius": "medium",
            "modal_radius": "large",
            "border_width": "thin",
            "shadow_intensity": "subtle",
            "content_width": "wide",
        },
        "storefront": {
            "layout": "brand",
            "mode": "default",
            "header": {"category_layout": "grid"},
            "marketplace": {
                "hero_layout": "both",
                "carousel_width": "full",
                "carousel_height": "medium",
                "autoplay": True,
                "interval": 7,
                "slides": [],
                "search_heading": "Find what you need. Discover what's next.",
                "search_description": "",
            },
            "background": {
                "type": "color",
                "color": "#FAF9F5",
                "gradient_from": "#FAF9F5",
                "gradient_to": "#E7F0EC",
                "gradient_angle": 135,
                "asset_id": "",
            },
            "hero": {
                "enabled": False,
                "type": "color",
                "heading": "",
                "description": "",
                "primary_cta_label": "",
                "primary_cta_url": "/shop",
                "secondary_cta_label": "",
                "secondary_cta_url": "",
                "alignment": "left",
                "position": "center_left",
                "overlay_color": "#000000",
                "overlay_opacity": 0.25,
                "minimum_height": "screen",
                "background_color": "#17362F",
                "gradient_from": "#17362F",
                "gradient_to": "#165B4C",
                "gradient_angle": 135,
                "asset_id": "",
                "poster_asset_id": "",
                "motion": "interactive",
            },
            "banner": {
                "enabled": False,
                "text": "",
                "background_color": "#17362F",
                "text_color": "#FFFFFF",
                "link_label": "",
                "link_url": "",
                "dismissible": True,
                "position": "top",
            },
            "popup": {
                "enabled": False,
                "mode": "standard",
                "title": "",
                "description": "",
                "asset_id": "",
                "cta_text": "",
                "cta_url": "",
                "background_color": "#FFFFFF",
                "text_color": "#17312B",
                "border_radius": "large",
                "display_delay": 5,
                "layout": "image_top",
                "size": "medium",
                "frequency": "session",
                "home_only": False,
                "dismissible": True,
                "custom_html": "",
                "custom_css": "",
            },
            "footer": {
                "description": "",
                "copyright_text": "",
                "logo_asset_id": "",
                "background_color": "#17362F",
                "text_color": "#FFFFFF",
                "link_color": "#D9F85D",
                "links": [],
                "custom_html": "",
                "custom_css": "",
            },
        },
        "socials": [],
        "workspace": {
            "use_business_branding": True,
            "sidebar_color": "#17362F",
            "header_color": "#FFFFFF",
            "background_color": "#F8F7F2",
        },
        "advanced": {
            "custom_html": "",
            "custom_css": "",
        },
    }


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _reject_unknown(value, template, path="branding"):
    if not isinstance(value, dict):
        raise serializers.ValidationError(f"{path} must be an object.")
    unknown = sorted(set(value) - set(template))
    if unknown:
        raise serializers.ValidationError({path: f"Unknown fields: {', '.join(unknown)}"})
    for key, child in value.items():
        if isinstance(child, dict) and isinstance(template.get(key), dict):
            _reject_unknown(child, template[key], f"{path}.{key}")


def _color(value, path):
    if not HEX_COLOR.fullmatch(str(value)):
        raise serializers.ValidationError({path: "Use a six-digit hex color."})


def _text(value, path, maximum):
    if not isinstance(value, str):
        raise serializers.ValidationError({path: "Use text."})
    value = value.strip()
    if len(value) > maximum:
        raise serializers.ValidationError({path: f"Use {maximum} characters or fewer."})
    return value


def _safe_link(value, path, https_only=False):
    value = _text(value, path, 500)
    if not value:
        return value
    if not https_only and value.startswith("/") and not value.startswith("//"):
        return value
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc:
        return value
    raise serializers.ValidationError({path: "Use an internal path or a complete HTTPS URL."})


def _asset_id(value, path):
    value = _text(value, path, 40)
    if not value:
        return ""
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise serializers.ValidationError({path: "Choose a valid business asset."}) from exc


def _integer(value, path):
    if isinstance(value, bool):
        raise serializers.ValidationError({path: "Use a whole number."})
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError({path: "Use a whole number."}) from exc


def _number(value, path):
    if isinstance(value, bool):
        raise serializers.ValidationError({path: "Use a number."})
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError({path: "Use a number."}) from exc


def _boolean(value, path):
    if not isinstance(value, bool):
        raise serializers.ValidationError({path: "Use true or false."})
    return value


class SafeCustomizationHTMLParser(HTMLParser):
    allowed_tags = {"p", "span", "strong", "em", "br", "a", "ul", "ol", "li", "h2", "h3", "blockquote", "small"}
    void_tags = {"br"}
    blocked_tags = {"script", "style", "iframe", "object", "embed", "svg", "math", "form", "input", "button", "video", "audio"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.blocked_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.blocked_tags:
            self.blocked_depth += 1
            return
        if self.blocked_depth or tag not in self.allowed_tags:
            return
        safe_attrs = []
        for name, value in attrs:
            name = name.lower()
            value = value or ""
            if name == "class":
                classes = [item for item in value.split() if CLASS_NAME.fullmatch(item)]
                if classes:
                    safe_attrs.append(("class", " ".join(classes)))
            elif tag == "a" and name == "href":
                try:
                    safe_attrs.append(("href", _safe_link(value, "custom_html.href")))
                except serializers.ValidationError:
                    continue
            elif tag == "a" and name == "target" and value == "_blank":
                safe_attrs.extend([("target", "_blank"), ("rel", "noopener noreferrer")])
            elif name in {"title", "aria-label"}:
                safe_attrs.append((name, value[:200]))
        rendered = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in safe_attrs)
        self.output.append(f"<{tag}{rendered}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in self.void_tags:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.blocked_tags:
            self.blocked_depth = max(0, self.blocked_depth - 1)
            return
        if not self.blocked_depth and tag in self.allowed_tags and tag not in self.void_tags:
            self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.blocked_depth:
            self.output.append(html.escape(data))


def sanitize_custom_html(value, path):
    value = _text(value, path, 20000)
    parser = SafeCustomizationHTMLParser()
    parser.feed(value)
    parser.close()
    return "".join(parser.output)


def validate_custom_css(value, path):
    value = _text(value, path, 12000)
    forbidden = re.compile(r"@(?:import|charset|namespace)|url\s*\(|expression\s*\(|javascript:|behavior\s*:|-moz-binding|</?style|[<>]", re.I)
    if forbidden.search(value):
        raise serializers.ValidationError({path: "Remote resources, imports, executable CSS, and markup are not allowed."})
    if value.count("{") != value.count("}"):
        raise serializers.ValidationError({path: "CSS blocks must have balanced braces."})
    return value


def normalize_identity_config(value):
    defaults = default_identity_config()
    _reject_unknown(value, defaults)
    compatible_value = copy.deepcopy(value)
    if "typography" not in compatible_value and compatible_value.get("font_family"):
        compatible_value["typography"] = {"primary_font": compatible_value["font_family"]}
    if "style" not in compatible_value and compatible_value.get("border_radius"):
        compatible_value["style"] = {
            "button_radius": compatible_value["border_radius"],
            "card_radius": compatible_value["border_radius"],
            "input_radius": compatible_value["border_radius"],
            "modal_radius": compatible_value["border_radius"],
        }
    config = deep_merge(defaults, compatible_value)
    if config["schema_version"] != 1:
        raise serializers.ValidationError({"schema_version": "Only identity schema version 1 is supported."})

    color_paths = [
        (config, key, key) for key in ("primary_color", "secondary_color", "accent_color", "background_color", "text_color", "muted_text_color", "link_color")
    ]
    color_paths += [
        (config["storefront"]["background"], key, f"storefront.background.{key}") for key in ("color", "gradient_from", "gradient_to")
    ]
    color_paths += [
        (config["storefront"]["hero"], key, f"storefront.hero.{key}") for key in ("overlay_color", "background_color", "gradient_from", "gradient_to")
    ]
    color_paths += [
        (config["storefront"]["banner"], key, f"storefront.banner.{key}") for key in ("background_color", "text_color")
    ]
    color_paths += [
        (config["storefront"]["popup"], key, f"storefront.popup.{key}") for key in ("background_color", "text_color")
    ]
    color_paths += [
        (config["storefront"]["footer"], key, f"storefront.footer.{key}") for key in ("background_color", "text_color", "link_color")
    ]
    color_paths += [
        (config["workspace"], key, f"workspace.{key}") for key in ("sidebar_color", "header_color", "background_color")
    ]
    for container, key, path in color_paths:
        _color(container[key], path)

    typography = config["typography"]
    for key in ("primary_font", "heading_font"):
        if typography[key] not in ALLOWED_FONTS:
            raise serializers.ValidationError({f"typography.{key}": "Choose an approved font."})
    if typography["body_weight"] not in {400, 500, 600} or typography["heading_weight"] not in {600, 700, 800}:
        raise serializers.ValidationError({"typography": "Choose an approved font weight."})
    if typography["base_font_size"] not in {"14px", "15px", "16px", "18px"}:
        raise serializers.ValidationError({"typography.base_font_size": "Choose an approved base size."})
    config["font_family"] = typography["primary_font"]
    config["heading_font_family"] = typography["heading_font"]

    style = config["style"]
    for key in ("button_radius", "card_radius", "input_radius", "modal_radius"):
        if style[key] not in ALLOWED_RADII:
            raise serializers.ValidationError({f"style.{key}": "Choose an approved radius."})
    if style["border_width"] not in {"none", "thin", "medium"}:
        raise serializers.ValidationError({"style.border_width": "Choose none, thin, or medium."})
    if style["shadow_intensity"] not in {"none", "subtle", "medium"}:
        raise serializers.ValidationError({"style.shadow_intensity": "Choose none, subtle, or medium."})
    if style["content_width"] not in {"compact", "standard", "wide", "full"}:
        raise serializers.ValidationError({"style.content_width": "Choose an approved content width."})
    config["border_radius"] = style["button_radius"]

    background = config["storefront"]["background"]
    if background["type"] not in {"color", "gradient", "image"}:
        raise serializers.ValidationError({"storefront.background.type": "Choose color, gradient, or image."})
    background["asset_id"] = _asset_id(background["asset_id"], "storefront.background.asset_id")
    background["gradient_angle"] = _integer(background["gradient_angle"], "storefront.background.gradient_angle")
    if not 0 <= background["gradient_angle"] <= 360:
        raise serializers.ValidationError({"storefront.background.gradient_angle": "Use an angle from 0 to 360."})

    header = config["storefront"]["header"]
    if config["storefront"]["layout"] not in {"brand", "marketplace"}:
        raise serializers.ValidationError(
            {"storefront.layout": "Choose brand or marketplace."}
        )
    if config["storefront"]["mode"] not in {"default", "luxury"}:
        raise serializers.ValidationError({"storefront.mode": "Choose default or luxury."})
    if header["category_layout"] not in {"grid", "carousel"}:
        raise serializers.ValidationError({"storefront.header.category_layout": "Choose grid or carousel."})

    marketplace = config["storefront"]["marketplace"]
    if not isinstance(marketplace, dict):
        raise serializers.ValidationError({"storefront.marketplace": "Use an object for marketplace settings."})
    for field, choices in {
        "hero_layout": {"search", "carousel", "both"},
        "carousel_width": {"full", "contained"},
        "carousel_height": {"compact", "medium", "tall", "screen"},
    }.items():
        if not isinstance(marketplace[field], str) or marketplace[field] not in choices:
            raise serializers.ValidationError({f"storefront.marketplace.{field}": "Choose an available presentation."})
    marketplace["autoplay"] = _boolean(marketplace["autoplay"], "storefront.marketplace.autoplay")
    marketplace["interval"] = _integer(marketplace["interval"], "storefront.marketplace.interval")
    if not 4 <= marketplace["interval"] <= 30:
        raise serializers.ValidationError({"storefront.marketplace.interval": "Use 4 to 30 seconds."})
    marketplace["search_heading"] = _text(marketplace["search_heading"], "storefront.marketplace.search_heading", 180)
    marketplace["search_description"] = _text(marketplace["search_description"], "storefront.marketplace.search_description", 600)
    from content.hero import validate_hero_slides
    marketplace["slides"] = validate_hero_slides(marketplace["slides"])

    hero = config["storefront"]["hero"]
    hero["enabled"] = _boolean(hero["enabled"], "storefront.hero.enabled")
    if hero["type"] not in {"color", "gradient", "image", "video", "three"}:
        raise serializers.ValidationError({"storefront.hero.type": "Choose color, gradient, image, video, or three."})
    if hero["alignment"] not in {"left", "center", "right"} or hero["position"] not in {"center_left", "center", "center_right", "bottom_left", "bottom_center", "bottom_right"}:
        raise serializers.ValidationError({"storefront.hero": "Choose an approved alignment and content position."})
    if hero["minimum_height"] not in {"compact", "medium", "tall", "screen"} or hero["motion"] not in {"none", "rotate", "interactive"}:
        raise serializers.ValidationError({"storefront.hero": "Choose approved height and motion settings."})
    hero["heading"] = _text(hero["heading"], "storefront.hero.heading", 180)
    hero["description"] = _text(hero["description"], "storefront.hero.description", 600)
    for key in ("primary_cta_label", "secondary_cta_label"):
        hero[key] = _text(hero[key], f"storefront.hero.{key}", 80)
    for key in ("primary_cta_url", "secondary_cta_url"):
        hero[key] = _safe_link(hero[key], f"storefront.hero.{key}")
    hero["asset_id"] = _asset_id(hero["asset_id"], "storefront.hero.asset_id")
    hero["poster_asset_id"] = _asset_id(hero["poster_asset_id"], "storefront.hero.poster_asset_id")
    hero["overlay_opacity"] = _number(hero["overlay_opacity"], "storefront.hero.overlay_opacity")
    hero["gradient_angle"] = _integer(hero["gradient_angle"], "storefront.hero.gradient_angle")
    if not 0 <= hero["overlay_opacity"] <= 0.9 or not 0 <= hero["gradient_angle"] <= 360:
        raise serializers.ValidationError({"storefront.hero": "Overlay opacity or gradient angle is out of range."})

    banner = config["storefront"]["banner"]
    banner["enabled"] = _boolean(banner["enabled"], "storefront.banner.enabled")
    banner["dismissible"] = _boolean(banner["dismissible"], "storefront.banner.dismissible")
    banner["text"] = _text(banner["text"], "storefront.banner.text", 240)
    banner["link_label"] = _text(banner["link_label"], "storefront.banner.link_label", 80)
    banner["link_url"] = _safe_link(banner["link_url"], "storefront.banner.link_url")
    if banner["position"] not in {"top", "below_header", "floating_bottom"}:
        raise serializers.ValidationError({"storefront.banner.position": "Choose an approved banner position."})

    popup = config["storefront"]["popup"]
    popup["enabled"] = _boolean(popup["enabled"], "storefront.popup.enabled")
    popup["home_only"] = _boolean(popup["home_only"], "storefront.popup.home_only")
    for field, choices in {
        "layout": {"image_top", "split", "poster"},
        "size": {"small", "medium", "large"},
        "frequency": {"session", "daily", "always"},
    }.items():
        if not isinstance(popup[field], str) or popup[field] not in choices:
            raise serializers.ValidationError({f"storefront.popup.{field}": "Choose an available popup option."})
    popup["dismissible"] = _boolean(popup["dismissible"], "storefront.popup.dismissible")
    if popup["mode"] not in {"standard", "custom"} or popup["border_radius"] not in ALLOWED_RADII:
        raise serializers.ValidationError({"storefront.popup": "Choose an approved mode and radius."})
    popup["title"] = _text(popup["title"], "storefront.popup.title", 120)
    popup["description"] = _text(popup["description"], "storefront.popup.description", 800)
    popup["cta_text"] = _text(popup["cta_text"], "storefront.popup.cta_text", 80)
    popup["cta_url"] = _safe_link(popup["cta_url"], "storefront.popup.cta_url")
    popup["asset_id"] = _asset_id(popup["asset_id"], "storefront.popup.asset_id")
    popup["display_delay"] = _integer(popup["display_delay"], "storefront.popup.display_delay")
    if not 0 <= popup["display_delay"] <= 120:
        raise serializers.ValidationError({"storefront.popup.display_delay": "Use a delay from 0 to 120 seconds."})
    popup["custom_html"] = sanitize_custom_html(popup["custom_html"], "storefront.popup.custom_html")
    popup["custom_css"] = validate_custom_css(popup["custom_css"], "storefront.popup.custom_css")

    footer = config["storefront"]["footer"]
    footer["description"] = _text(footer["description"], "storefront.footer.description", 500)
    footer["copyright_text"] = _text(footer["copyright_text"], "storefront.footer.copyright_text", 180)
    footer["logo_asset_id"] = _asset_id(footer["logo_asset_id"], "storefront.footer.logo_asset_id")
    if not isinstance(footer["links"], list) or len(footer["links"]) > 8:
        raise serializers.ValidationError({"storefront.footer.links": "Add no more than eight links."})
    normalized_links = []
    for index, item in enumerate(footer["links"]):
        if not isinstance(item, dict) or set(item) - {"label", "url"}:
            raise serializers.ValidationError({"storefront.footer.links": "Each link needs only a label and URL."})
        normalized_links.append({"label": _text(item.get("label", ""), f"storefront.footer.links.{index}.label", 80), "url": _safe_link(item.get("url", ""), f"storefront.footer.links.{index}.url")})
    footer["links"] = normalized_links
    footer["custom_html"] = sanitize_custom_html(footer["custom_html"], "storefront.footer.custom_html")
    footer["custom_css"] = validate_custom_css(footer["custom_css"], "storefront.footer.custom_css")

    if not isinstance(config["socials"], list) or len(config["socials"]) > 8:
        raise serializers.ValidationError({"socials": "Add no more than eight social links."})
    socials = []
    for index, item in enumerate(config["socials"]):
        if not isinstance(item, dict) or set(item) - {"platform", "url"}:
            raise serializers.ValidationError({"socials": "Each social link needs only a platform and URL."})
        platform = _text(item.get("platform", ""), f"socials.{index}.platform", 32).lower()
        if not PLATFORM_NAME.fullmatch(platform):
            raise serializers.ValidationError({f"socials.{index}.platform": "Use a short platform name."})
        socials.append({"platform": platform, "url": _safe_link(item.get("url", ""), f"socials.{index}.url", https_only=True)})
    config["socials"] = socials

    advanced = config["advanced"]
    config["workspace"]["use_business_branding"] = _boolean(config["workspace"]["use_business_branding"], "workspace.use_business_branding")
    advanced["custom_html"] = sanitize_custom_html(advanced["custom_html"], "advanced.custom_html")
    advanced["custom_css"] = validate_custom_css(advanced["custom_css"], "advanced.custom_css")
    return config


def referenced_asset_ids(config):
    values = set()

    def visit(value, key=""):
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, child_key)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif key.endswith("asset_id") and value:
            values.add(str(value))

    visit(config)
    return values
