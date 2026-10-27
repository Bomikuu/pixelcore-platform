from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from businesses.models import Business, BusinessMembership
from catalog.models import Category, Offering
from commerce.models import Order, OrderItem


class BusinessAnalyticsTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("analytics-owner", password="test-password")
        self.business = Business.objects.create(display_name="Analytics studio", created_by=self.owner)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")
        self.client.force_authenticate(self.owner)
        self.offering = Offering.objects.create(business=self.business, name="Studio kit", base_price="100.00")
        self.url = f"/api/businesses/{self.business.public_id}/reports/"

    def order(self, number, *, business=None, status="pending", at=None, amount="100.00"):
        order = Order.objects.create(
            business=business or self.business, number=number, status=status,
            currency="PHP", subtotal=amount, grand_total=amount,
            customer_snapshot={"first_name": "Alex", "last_name": "Rivera"},
        )
        Order.objects.filter(pk=order.pk).update(placed_at=at or datetime(2026, 10, 1, 12, tzinfo=datetime_timezone.utc))
        return order

    def line(self, order, *, offering=None, quantity=1, amount="100.00"):
        return OrderItem.objects.create(
            order=order, offering=offering or self.offering, name=(offering or self.offering).name,
            quantity=quantity, unit_price="100.00", line_total=amount,
            offering_snapshot={"unit_cost": "20.00"},
        )

    def report(self, **query):
        return self.client.get(self.url, {"date_from": "2026-10-01", "date_to": "2026-10-02", **query})

    def test_complete_period_is_not_limited_to_latest_hundred_orders(self):
        for index in range(105):
            self.line(self.order(f"A-{index}"))
        self.line(self.order("cancelled", status="cancelled", amount="900.00"), amount="900.00")
        self.line(self.order("outside-period", at=datetime(2026, 9, 29, 12, tzinfo=datetime_timezone.utc)))
        other = Business.objects.create(display_name="Other tenant", created_by=self.owner)
        self.order("other-tenant", business=other, amount="99999.00")

        response = self.report()
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["sales"], Decimal("10500.00"))
        self.assertEqual(data["orders"]["total"], 105)
        self.assertEqual(data["gross_profit"], Decimal("8400.00"))
        self.assertEqual(sum(day["sales"] for day in data["daily_activity"]), data["sales"])
        self.assertEqual(sum(day["orders"] for day in data["daily_activity"]), 105)
        self.assertEqual(data["daily_activity"][1]["orders"], 0)
        self.assertEqual(data["analytics"]["top_products"][0]["quantity"], 105)
        self.assertEqual(data["analytics"]["product_summary"], {"units_sold": 105, "products_sold": 1, "categories_sold": 1})
        self.assertEqual(data["analytics"]["top_products"][0]["sales"], data["sales"])
        self.assertEqual(data["analytics"]["orders_placed"], 106)
        self.assertEqual(len(data["analytics"]["recent_orders"]), 5)
        self.assertEqual(data["analytics"]["recent_orders"][0]["customer_name"], "Alex Rivera")

    def test_product_order_count_is_distinct_and_unlinked_items_remain_in_totals(self):
        order = self.order("variants", amount="500.00")
        self.line(order, quantity=2, amount="200.00")
        self.line(order, quantity=3, amount="300.00")
        data = self.report().data
        product = data["analytics"]["top_products"][0]
        self.assertEqual((product["quantity"], product["orders"], product["sales"]), (5, 1, Decimal("500.00")))
        self.offering.delete()
        data = self.report().data
        self.assertEqual(data["analytics"]["item_sales"], Decimal("500.00"))
        self.assertEqual(data["analytics"]["categories"][0]["name"], "Uncategorized")
        self.assertEqual(data["analytics"]["top_products"][0]["image_url"], "")

    def test_business_timezone_controls_period_boundaries_and_daily_buckets(self):
        self.business.timezone = "America/Los_Angeles"
        self.business.save(update_fields=["timezone"])
        self.line(self.order("local-october-first", at=datetime(2026, 10, 2, 2, tzinfo=datetime_timezone.utc)))
        self.line(self.order("local-october-second", at=datetime(2026, 10, 2, 10, tzinfo=datetime_timezone.utc)))
        response = self.report(date_to="2026-10-01")
        self.assertEqual(response.data["timezone"], "America/Los_Angeles")
        self.assertEqual(response.data["orders"]["total"], 1)
        self.assertEqual(response.data["daily_activity"][0]["sales"], Decimal("100.00"))

    def test_category_tail_is_included_in_other_instead_of_dropped(self):
        for index in range(7):
            category = Category.objects.create(business=self.business, name=f"Category {index}", slug=f"cat-{index}")
            offering = Offering.objects.create(business=self.business, category=category, name=f"Item {index}", base_price="100.00")
            self.line(self.order(f"C-{index}"), offering=offering)
        data = self.report().data["analytics"]
        self.assertEqual(len(data["categories"]), 6)
        self.assertEqual(data["categories"][-1], {"name": "Other categories", "sales": Decimal("200.00")})
        self.assertEqual(sum(row["sales"] for row in data["categories"]), data["item_sales"])
        self.assertEqual(len(data["top_products"]), 6)
        self.assertEqual(data["product_summary"], {"units_sold": 7, "products_sold": 7, "categories_sold": 7})

    def test_empty_invalid_and_unauthorized_reports(self):
        empty = self.report()
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.data["analytics"]["top_products"], [])
        self.assertEqual(empty.data["analytics"]["orders_placed"], 0)
        self.assertEqual(empty.data["analytics"]["product_summary"], {"units_sold": 0, "products_sold": 0, "categories_sold": 0})
        self.assertEqual(len(empty.data["daily_activity"]), 2)
        self.assertEqual(self.report(date_to="2026-09-01").status_code, 400)
        self.assertEqual(self.report(date_to="invalid").status_code, 400)
        outsider = get_user_model().objects.create_user("analytics-outsider", password="test-password")
        self.client.force_authenticate(outsider)
        self.assertEqual(self.report().status_code, 404)
