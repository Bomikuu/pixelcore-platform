from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from catalog.models import Category, Offering, OfferingMedia, OfferingVariant
from commerce.models import Discount
from scheduling.models import StaffProfile
from .models import Business, BusinessAsset, BusinessCapability, BusinessMembership


class WorkspaceSearchTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="workspace-search")
        self.business = Business.objects.create(
            display_name="Search shop", created_by=self.user, enabled_modules=["sell", "operate"]
        )
        self.membership = BusinessMembership.objects.create(business=self.business, user=self.user, role="owner")
        self.other = Business.objects.create(display_name="Other shop", created_by=self.user)
        self.product = Offering.objects.create(business=self.business, name="Canvas tote", offering_type="physical", sku="TOTE-01")
        OfferingVariant.objects.create(offering=self.product, price=100, name="Natural", sku="TOTE-NAT", barcode="1234567890123")
        Offering.objects.create(business=self.other, name="Private canvas tote", offering_type="physical")
        self.promo = Discount.objects.create(business=self.business, name="Weekend offer", code="SAVE10", value_type="percentage", value=10)
        Category.objects.create(business=self.business, name="Everyday carry")
        self.employee = StaffProfile.objects.create(business=self.business, display_name="Alex Rivera", job_title="Store lead", emergency_contact_name="Private contact")
        self.url = reverse("workspace-search", kwargs={"public_id": self.business.public_id})
        self.client.force_authenticate(self.user)

    def search(self, **query):
        response = self.client.get(self.url, query)
        self.assertEqual(response.status_code, 200, response.data)
        return {group["kind"]: group["items"] for group in response.data["groups"]}

    def test_suggestions_are_grouped_minimal_and_tenant_scoped(self):
        groups = self.search()
        self.assertEqual(set(groups), {"products", "promotions", "categories", "employees"})
        self.assertEqual([item["name"] for item in groups["products"]], ["Canvas tote"])
        self.assertEqual(set(groups["employees"][0]), {"public_id", "name", "detail", "status", "image_url"})
        self.assertNotIn("Private contact", str(groups))
        self.assertEqual(self.client.get(self.url)["Cache-Control"], "private, no-store")

    def image_asset(self, name, **overrides):
        return BusinessAsset.objects.create(**{
            "business": self.business, "title": name, "asset_type": "image",
            "file": f"search/{name}.png", "mime_type": "image/png",
            "size_bytes": 10, "uploaded_by": self.user, **overrides,
        })

    def test_images_use_product_cover_category_cover_and_employee_photo(self):
        cover = self.image_asset("cover")
        gallery = self.image_asset("gallery")
        OfferingMedia.objects.create(business=self.business, offering=self.product, asset=gallery, role="gallery", sort_order=0)
        OfferingMedia.objects.create(business=self.business, offering=self.product, asset=cover, role="cover", sort_order=10)
        Category.objects.filter(business=self.business).update(cover_asset=cover)
        self.employee.profile_image = "search/employee.png"
        self.employee.save()
        groups = self.search()
        self.assertTrue(groups["products"][0]["image_url"].endswith("/search/cover.png"))
        self.assertTrue(groups["categories"][0]["image_url"].endswith("/search/cover.png"))
        self.assertTrue(groups["employees"][0]["image_url"].endswith("/search/employee.png"))
        self.assertEqual(groups["promotions"][0]["image_url"], "")

    def test_legacy_image_fallback_excludes_unready_and_foreign_assets(self):
        legacy = self.image_asset("legacy")
        unready = self.image_asset("unready", processing_status="processing")
        foreign = self.image_asset("private", business=self.other)
        self.product.assets.add(legacy, foreign, unready)
        OfferingMedia.objects.create(business=self.business, offering=self.product, asset=unready, role="cover")
        OfferingMedia.objects.create(business=self.business, offering=self.product, asset=foreign, role="gallery")
        Category.objects.filter(business=self.business).update(cover_asset=foreign)
        groups = self.search()
        self.assertTrue(groups["products"][0]["image_url"].endswith("/search/legacy.png"))
        self.assertEqual(groups["categories"][0]["image_url"], "")
        self.assertEqual(groups["employees"][0]["image_url"], "")

    def test_name_sku_barcode_promotion_code_and_employee_code(self):
        for term in ["canvas tote", "TOTE-01", "TOTE-NAT", "1234567890123"]:
            with self.subTest(term=term):
                self.assertEqual(self.search(search=term)["products"][0]["public_id"], str(self.product.public_id))
        self.assertEqual(self.search(search="SAVE10")["promotions"][0]["public_id"], str(self.promo.public_id))
        self.assertEqual(self.search(search=self.employee.employee_code)["employees"][0]["public_id"], str(self.employee.public_id))
        self.assertEqual(self.search(search="store lead")["employees"][0]["name"], "Alex Rivera")

    def test_type_filters_aliases_and_empty_results(self):
        self.assertEqual(set(self.search(scope="categories")), {"categories"})
        self.assertEqual(set(self.search(search="promo")), {"promotions"})
        self.assertEqual(self.search(search="products canvas")["products"][0]["name"], "Canvas tote")
        self.assertTrue(all(not items for items in self.search(search="no-such-record").values()))
        self.assertEqual(self.client.get(self.url, {"scope": "secrets"}).status_code, 400)
        self.assertEqual(self.client.get(self.url, {"search": "x" * 121}).status_code, 400)

    def test_suggestions_and_matches_are_bounded_and_variants_deduplicated(self):
        for number in range(8):
            Offering.objects.create(business=self.business, name=f"Canvas bag {number}", offering_type="physical")
        OfferingVariant.objects.create(offering=self.product, price=100, name="Olive", sku="TOTE-OLV")
        self.assertEqual(len(self.search()["products"]), 3)
        self.assertEqual(len(self.search(search="canvas")["products"]), 5)
        self.assertEqual(len(self.search(search="TOTE")["products"]), 1)

    def test_roles_match_employee_destination_and_inactive_members_cannot_search(self):
        for role in ["manager", "staff"]:
            self.membership.role = role
            self.membership.save()
            self.assertNotIn("employees", self.search())
            self.assertIn("products", self.search())
        self.membership.status = "suspended"
        self.membership.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_modules_and_membership_gate_all_results(self):
        BusinessCapability.objects.create(business=self.business, code="sell", status="disabled")
        BusinessCapability.objects.create(business=self.business, code="operate", status="active")
        self.assertEqual(set(self.search()), {"employees"})
        BusinessCapability.objects.filter(business=self.business).update(status="disabled")
        self.assertEqual(self.search(), {})
        self.assertEqual(self.client.get(reverse("workspace-search", kwargs={"public_id": self.other.public_id})).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
