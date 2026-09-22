from django.test import SimpleTestCase
from rest_framework.serializers import ValidationError

from .serializers import validate_display_settings


class DisplaySettingsValidationTests(SimpleTestCase):
    def valid_settings(self):
        return {
            "background": "#102a2a",
            "foreground": "#f7f3ea",
            "builder": {
                "slides": [{
                    "id": "main",
                    "duration_seconds": 8,
                    "elements": [{
                        "id": "heading",
                        "type": "heading",
                        "x": 7,
                        "y": 12,
                        "width": 50,
                        "height": 16,
                        "rotation": 0,
                        "z_index": 10,
                        "content": "Seasonal collection",
                        "style": {"font_family": "newsreader", "font_size": 64, "font_weight": 700, "color": "#f7f3ea", "text_align": "left"},
                    }],
                }],
            },
        }

    def test_accepts_bounded_structured_layout(self):
        value = self.valid_settings()
        self.assertEqual(validate_display_settings(value), value)

    def test_rejects_executable_and_raw_style_fields(self):
        for field in ("javascript", "html", "css"):
            value = self.valid_settings()
            value["builder"]["slides"][0]["elements"][0][field] = "alert(1)"
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_display_settings(value)

    def test_rejects_unapproved_font_and_geometry(self):
        value = self.valid_settings()
        value["builder"]["slides"][0]["elements"][0]["style"]["font_family"] = "url(evil)"
        with self.assertRaises(ValidationError):
            validate_display_settings(value)

        value = self.valid_settings()
        value["builder"]["slides"][0]["elements"][0]["width"] = 101
        with self.assertRaises(ValidationError):
            validate_display_settings(value)
