from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from businesses.models import Business
from commerce.models import Customer, Order, OrderItem
from .models import Offering, ProductReview


class ProductReviewTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.buyer = user_model.objects.create_user(username="review-buyer", first_name="Sam", email="buyer@example.com")
        self.other = user_model.objects.create_user(username="review-other", email="other@example.com")
        self.business = Business.objects.create(display_name="Review Store", created_by=self.buyer, status="active")
        self.product = Offering.objects.create(business=self.business, name="Travel Bag", base_price=100, status="published")
        customer = Customer.objects.create(business=self.business, user=self.buyer, email=self.buyer.email)
        self.order = Order.objects.create(
            business=self.business, customer=customer, number="REVIEW-1", currency="PHP",
            subtotal=100, grand_total=100, payment_status="paid", status="confirmed",
        )
        OrderItem.objects.create(order=self.order, offering=self.product, name=self.product.name, quantity=1, unit_price=100, line_total=100)
        self.path = f"/api/public/{self.business.slug}/storefront/products/{self.product.slug}/reviews/"
        self.payload = {"rating": 4, "title": "Useful everyday bag", "body": "Enough room for my commute."}

    def test_public_empty_and_auth_required(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["count"], 0)
        self.assertIsNone(response.data["summary"]["average"])
        self.assertEqual(self.client.put(self.path + "mine/", self.payload).status_code, 401)

    def test_purchase_required_and_cancelled_order_rejected(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.put(self.path + "mine/", self.payload).status_code, 403)
        self.client.force_authenticate(self.buyer)
        self.order.status = "cancelled"
        self.order.save()
        self.assertEqual(self.client.put(self.path + "mine/", self.payload).status_code, 403)

    def test_update_is_idempotent_and_public_fields_are_allowlisted(self):
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.put(self.path + "mine/", self.payload).status_code, 201)
        response = self.client.put(self.path + "mine/", {**self.payload, "rating": 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductReview.objects.count(), 1)
        response = self.client.get(self.path)
        self.assertEqual(response.data["summary"]["average"], 5)
        self.assertEqual(response.data["summary"]["distribution"][0]["count"], 1)
        self.assertEqual(response.data["results"][0]["author_name"], "Sam")
        self.assertNotIn("email", response.data["results"][0])
        self.assertNotIn("author", response.data["results"][0])
        self.assertTrue(response.data["results"][0]["verified_purchase"])

    def test_validation_and_plain_text(self):
        self.client.force_authenticate(self.buyer)
        for payload in [{**self.payload, "rating": 6}, {**self.payload, "rating": 0}, {**self.payload, "title": " "}, {**self.payload, "body": "x" * 3001}]:
            self.assertEqual(self.client.put(self.path + "mine/", payload).status_code, 400)
        response = self.client.put(self.path + "mine/", {**self.payload, "body": "<script>alert(1)</script>"})
        self.assertEqual(response.status_code, 201)
        # API content is plain text; the Vue consumer uses escaped interpolation.
        self.assertEqual(response.data["body"], "<script>alert(1)</script>")

    def test_hidden_review_stays_hidden_on_edit(self):
        ProductReview.objects.create(offering=self.product, author=self.buyer, is_visible=False, **self.payload)
        self.client.force_authenticate(self.buyer)
        self.client.put(self.path + "mine/", {**self.payload, "is_visible": True})
        self.assertEqual(self.client.get(self.path).data["count"], 0)
        self.assertFalse(self.client.get(self.path + "mine/").data["is_visible"])

    def test_pagination_rating_filter_and_own_delete(self):
        ProductReview.objects.create(offering=self.product, author=self.buyer, **self.payload)
        for index in range(6):
            author = get_user_model().objects.create_user(username=f"review-{index}")
            ProductReview.objects.create(offering=self.product, author=author, rating=5, title="Good", body="Review body")
        response = self.client.get(self.path)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(self.client.get(self.path, {"page": 2}).data["results"]), 2)
        filtered = self.client.get(self.path, {"rating": 4})
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["summary"]["count"], 7)
        self.assertEqual(self.client.get(self.path, {"rating": "bad"}).status_code, 400)
        self.client.force_authenticate(self.other)
        self.client.delete(self.path + "mine/")
        self.assertEqual(ProductReview.objects.count(), 7)
        self.client.force_authenticate(self.buyer)
        self.client.delete(self.path + "mine/")
        self.assertEqual(ProductReview.objects.count(), 6)

    def test_unpublished_and_other_tenant_purchase_are_rejected(self):
        another = Business.objects.create(display_name="Another Store", created_by=self.other, status="active")
        product = Offering.objects.create(business=another, name=self.product.name, base_price=100, status="published")
        path = f"/api/public/{another.slug}/storefront/products/{product.slug}/reviews/"
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.put(path + "mine/", self.payload).status_code, 403)
        self.product.status = "draft"
        self.product.save()
        self.assertEqual(self.client.get(self.path).status_code, 404)
        self.assertEqual(self.client.put(self.path + "mine/", self.payload).status_code, 404)
