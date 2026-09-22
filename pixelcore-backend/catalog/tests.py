import json
import struct

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from businesses.models import Business, BusinessMembership
from .glb import validate_glb
from .models import Category, Offering, OfferingVariant, ProductCollection, ProductProfile


User = get_user_model()


def glb_upload(document):
    body = json.dumps(document, separators=(",", ":")).encode()
    body += b" " * ((4 - len(body) % 4) % 4)
    payload = struct.pack("<4sII", b"glTF", 2, 20 + len(body)) + struct.pack("<II", len(body), 0x4E4F534A) + body
    return SimpleUploadedFile("product.glb", payload, content_type="model/gltf-binary")


class CommerceCatalogTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="commerce-owner", email="owner@example.com", password="SafePassphrase123!")
        self.other = User.objects.create_user(username="commerce-other", email="other@example.com", password="SafePassphrase123!")
        self.business = Business.objects.create(display_name="Field Supply", status="active", created_by=self.owner)
        self.other_business = Business.objects.create(display_name="Other Supply", status="active", created_by=self.other)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")
        BusinessMembership.objects.create(business=self.other_business, user=self.other, role="owner")
        self.product = Offering.objects.create(business=self.business, name="Everyday Carry", offering_type="physical", fulfillment_type="delivery", base_price="1290", status="published")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.owner).access_token}")

    def test_variant_matrix_is_atomic_and_preserves_product_scope(self):
        path = f"/api/businesses/{self.business.public_id}/offerings/{self.product.public_id}/variant-matrix/"
        response = self.client.put(path, {
            "dimensions": [
                {"name": "Size", "display_type": "text", "values": [{"label": "S"}, {"label": "M"}]},
                {"name": "Color", "display_type": "color", "values": [{"label": "Ink", "swatch_color": "#112233"}]},
            ],
            "variants": [
                {"options": {"Size": "S", "Color": "Ink"}, "sku": "EC-S-I", "barcode": "10001", "price": "1290.00", "unit_cost": "600", "is_active": True},
                {"options": {"Size": "M", "Color": "Ink"}, "sku": "EC-M-I", "barcode": "10002", "price": "1390.00", "unit_cost": "650", "is_active": True},
            ],
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["dimensions"]), 2)
        self.assertEqual(self.product.variants.count(), 2)
        self.assertTrue(all(variant.combination_key for variant in self.product.variants.all()))

    def test_collection_rejects_another_business_product(self):
        other_product = Offering.objects.create(business=self.other_business, name="Private", offering_type="physical", base_price="10")
        response = self.client.post(f"/api/businesses/{self.business.public_id}/collections/", {"name": "Essentials", "offering_public_ids": [str(other_product.public_id)]}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ProductCollection.objects.exists())

    def test_collection_hero_accepts_only_products_in_the_collection(self):
        second = Offering.objects.create(business=self.business, name="Travel Pack", offering_type="physical", base_price="2190", status="published")
        response = self.client.post(
            f"/api/businesses/{self.business.public_id}/collections/",
            {
                "name": "Essentials",
                "offering_public_ids": [str(self.product.public_id), str(second.public_id)],
                "hero_settings": {
                    "enabled": True,
                    "heading": "Objects for the everyday route",
                    "body": "A focused edit of daily equipment.",
                    "offering_ids": [str(second.public_id)],
                    "autoplay": False,
                },
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["hero_settings"]["offering_ids"], [str(second.public_id)])

        response = self.client.patch(
            f"/api/businesses/{self.business.public_id}/collections/{response.data['public_id']}/",
            {"hero_settings": {"enabled": True, "offering_ids": [str(self.other_business.public_id)]}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_public_commerce_endpoint_is_paginated_and_excludes_drafts(self):
        Offering.objects.create(business=self.business, name="Hidden", offering_type="physical", base_price="50", status="draft")
        OfferingVariant.objects.create(offering=self.product, name="Standard", sku="PUBLIC-SKU", price="1290", unit_cost="400")
        self.client.credentials()
        response = self.client.get(f"/api/public/{self.business.slug}/storefront/products/?search=Everyday")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["public_id"], str(self.product.public_id))
        self.assertIn("facets", response.data)
        self.assertNotIn("unit_cost", response.data["results"][0]["variants"][0])

    def test_storefront_highlight_moves_between_products(self):
        second = Offering.objects.create(business=self.business, name="Travel Pack", offering_type="physical", fulfillment_type="delivery", base_price="2190", status="published")
        for offering in (self.product, second):
            response = self.client.patch(
                f"/api/businesses/{self.business.public_id}/offerings/{offering.public_id}/",
                {"product_profile": {"storefront_highlighted": True}},
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(ProductProfile.objects.filter(business=self.business, storefront_highlighted=True).count(), 1)
        self.assertTrue(ProductProfile.objects.get(offering=second).storefront_highlighted)
        self.client.credentials()
        response = self.client.get(f"/api/public/{self.business.slug}/storefront/products/")
        self.assertEqual(response.data["highlighted"]["public_id"], str(second.public_id))

    def test_public_category_facets_expose_header_curation(self):
        category = Category.objects.create(business=self.business, name="Travel", show_in_header=False, header_order=8)
        self.product.category = category
        self.product.save(update_fields=["category"])
        self.client.credentials()
        response = self.client.get(f"/api/public/{self.business.slug}/storefront/products/")
        facet = response.data["facets"]["categories"][0]
        self.assertEqual(facet["slug"], category.slug)
        self.assertFalse(facet["show_in_header"])
        self.assertEqual(facet["header_order"], 8)

    def test_glb_validator_rejects_external_resources(self):
        upload = glb_upload({"asset": {"version": "2.0"}, "buffers": [{"uri": "mesh.bin", "byteLength": 12}]})
        metadata, error = validate_glb(upload)
        self.assertIsNone(metadata)
        self.assertIn("external file", error)

    def test_glb_validator_accepts_self_contained_scene(self):
        upload = glb_upload({"asset": {"version": "2.0"}, "scenes": [{"nodes": []}], "nodes": []})
        metadata, error = validate_glb(upload)
        self.assertEqual(error, "")
        self.assertEqual(metadata["glb_version"], 2)
