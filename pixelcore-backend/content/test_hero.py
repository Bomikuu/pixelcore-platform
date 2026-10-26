from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from businesses.models import Business, BusinessAsset
from catalog.models import ProductCollection
from catalog.serializers import ProductCollectionSerializer, PublicProductCollectionSerializer
from .hero import validate_hero_slides
from .models import Site, SitePage
from .services import create_revision, publish_revision


class CustomHeroTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('hero-owner')
        self.business = Business.objects.create(display_name='Hero studio', created_by=self.user)
        self.image = BusinessAsset.objects.create(business=self.business, uploaded_by=self.user, title='Poster', asset_type='image', file='hero/poster.png', size_bytes=100, processing_status='ready')
        self.slide = {'id': 'custom-1', 'type': 'image', 'heading': 'A custom story', 'asset_id': str(self.image.public_id), 'path': '/shop', 'label': 'Explore'}

    def test_custom_collection_slides_and_public_media(self):
        serializer = ProductCollectionSerializer(data={'name': 'Story', 'hero_settings': {'slides': [self.slide]}}, context={'business': self.business})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(business=self.business)
        payload = PublicProductCollectionSerializer(item).data
        self.assertEqual(payload['hero_settings']['slides'][0]['heading'], 'A custom story')
        self.assertEqual(payload['hero_assets'][0]['public_id'], str(self.image.public_id))

    def test_rejects_unsafe_media_and_malformed_values(self):
        other = Business.objects.create(display_name='Other', created_by=self.user)
        for slide in [{**self.slide, 'type': []}, {**self.slide, 'motion': {}}, {**self.slide, 'path': 'https://other.test'}, {**self.slide, 'script': 'alert(1)'}]:
            with self.assertRaises(ValidationError): validate_hero_slides([slide], self.business)
        with self.assertRaises(ValidationError): validate_hero_slides([self.slide], other)
        with self.assertRaises(ValidationError): validate_hero_slides([self.slide] * 6, self.business)

    def test_video_and_model_require_correct_approved_media_and_poster(self):
        for kind in ['video', 'model']:
            media = BusinessAsset.objects.create(business=self.business, uploaded_by=self.user, title=kind, asset_type=kind, file=f'hero/{kind}', size_bytes=100, processing_status='ready')
            slide = {**self.slide, 'type': kind, 'asset_id': str(media.public_id)}
            with self.assertRaises(ValidationError): validate_hero_slides([slide], self.business)
            slide['poster_asset_id'] = str(self.image.public_id)
            self.assertEqual(validate_hero_slides([slide], self.business)[0]['type'], kind)
            media.processing_status = 'rejected'; media.save()
            with self.assertRaises(ValidationError): validate_hero_slides([slide], self.business)

    def test_cms_publish_revalidates_custom_assets(self):
        site = Site.objects.create(business=self.business, name='Studio')
        page = SitePage.objects.create(site=site, title='Home', slug='home', page_type='home')
        revision = create_revision(page, {'schema_version': 1, 'blocks': [{'id': 'hero', 'type': 'commerce_hero', 'version': 1, 'settings': {'slides': [self.slide]}}]}, self.user)
        self.image.processing_status = 'rejected'; self.image.save()
        with self.assertRaises(ValidationError): publish_revision(page, revision, self.user)
        page.refresh_from_db(); self.assertIsNone(page.published_revision)
