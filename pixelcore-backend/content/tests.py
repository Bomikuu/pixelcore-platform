from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from businesses.models import Business
from .blocks import validate_page_content
from .models import Site, SitePage
from .services import create_revision, publish_revision


class ContentRevisionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="North Star Studio", created_by=self.user)
        self.site = Site.objects.create(business=self.business, name="North Star Studio")
        self.page = SitePage.objects.create(site=self.site, title="Home", slug="home", page_type="home")

    def test_rejects_executable_content(self):
        content = {"schema_version": 1, "blocks": [{"id": "hero-1", "type": "hero", "version": 1, "settings": {"heading": "Hello", "javascript": "alert(1)"}}]}
        with self.assertRaises(ValidationError):
            validate_page_content(content)

    def test_publishing_preserves_prior_immutable_revision(self):
        first = create_revision(self.page, {"schema_version": 1, "blocks": []}, self.user)
        second = create_revision(self.page, {"schema_version": 1, "blocks": [{"id": "copy", "type": "text", "version": 1, "settings": {"document": ["Updated"]}}]}, self.user)
        publish_revision(self.page, second, self.user)

        first.refresh_from_db()
        self.page.refresh_from_db()
        self.assertEqual(first.content["blocks"], [])
        self.assertEqual(self.page.published_revision, second)
        self.assertEqual(self.site.__class__.objects.get(pk=self.site.pk).cache_version, 2)
