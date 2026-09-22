from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from .identity import normalize_identity_config, referenced_asset_ids


class StorefrontCampaignSettingsTests(SimpleTestCase):
    def test_existing_identity_gets_compatible_defaults(self):
        config = normalize_identity_config({})["storefront"]
        self.assertEqual(config["marketplace"]["hero_layout"], "both")
        self.assertEqual(config["popup"]["layout"], "image_top")
        self.assertFalse(config["popup"]["enabled"])

    def test_carousel_and_popup_options_round_trip(self):
        config = normalize_identity_config({"storefront": {
            "marketplace": {"hero_layout": "carousel", "carousel_width": "contained", "interval": 10},
            "popup": {"layout": "poster", "size": "large", "frequency": "daily", "home_only": True},
        }})
        self.assertEqual(config["storefront"]["marketplace"]["interval"], 10)
        self.assertEqual(config["storefront"]["popup"]["frequency"], "daily")

    def test_invalid_options_are_rejected(self):
        for section, field, value in [
            ("marketplace", "interval", 1),
            ("marketplace", "hero_layout", "invalid"),
            ("marketplace", "slides", [{}] * 6),
            ("popup", "frequency", "invalid"),
            ("popup", "size", "huge"),
        ]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                normalize_identity_config({"storefront": {section: {field: value}}})

    def test_slide_assets_are_discovered_and_links_validated(self):
        asset_id = "a3f8e773-69b8-4259-ae8a-0f6710671cfb"
        slide = {"id": "launch", "type": "image", "asset_id": asset_id, "path": "/shop"}
        config = normalize_identity_config({"storefront": {"marketplace": {"slides": [slide]}}})
        self.assertEqual(referenced_asset_ids(config), {asset_id})
        with self.assertRaises(ValidationError):
            normalize_identity_config({"storefront": {"marketplace": {"slides": [{**slide, "path": "https://example.com"}]}}})
