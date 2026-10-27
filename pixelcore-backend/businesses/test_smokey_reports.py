from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from scheduling.models import StaffProfile
from workforce.models import AttendanceRecord
from commerce.models import Order
from smokey_assistant.contracts import HostContext, ReportPlan
from .models import Business
from .smokey_reports import resolve_report


class SmokeyReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="facts")
        self.business = Business.objects.create(
            display_name="Facts", created_by=self.user
        )
        self.context = HostContext(
            f"pixelcore:{self.business.public_id}",
            str(self.user.pk),
            "Asia/Manila",
            frozenset({"generate"}),
        )
        self.staff = StaffProfile.objects.create(
            business=self.business,
            display_name="Alex",
            emergency_contact_name="Private",
        )

    def report(self, kind="attendance"):
        return resolve_report(
            self.context,
            ReportPlan.parse(
                {"kind": kind, "date_from": "2026-10-26", "date_to": "2026-10-26"}
            ),
        )

    def test_distinct_counts_timezone_and_private_fields(self):
        for hour in (1, 4):
            AttendanceRecord.objects.create(
                business=self.business,
                staff=self.staff,
                clock_in=datetime(2026, 10, 26, hour, tzinfo=dt_timezone.utc),
                clock_out=datetime(2026, 10, 26, hour + 1, tzinfo=dt_timezone.utc),
                late_minutes=5,
                late_excused=True,
                late_reason="Private reason",
            )
        # UTC Oct 26 17:00 is Oct 27 in Manila and must be excluded.
        AttendanceRecord.objects.create(
            business=self.business,
            staff=self.staff,
            clock_in=datetime(2026, 10, 26, 17, tzinfo=dt_timezone.utc),
            late_minutes=50,
        )
        result = self.report()
        self.assertEqual(result.facts["metrics"]["attended_employees"], 1)
        self.assertEqual(result.facts["metrics"]["late_employees"], 1)
        self.assertEqual(result.facts["metrics"]["excused_late_employees"], 1)
        self.assertNotIn("Private", str(result.facts))
        self.assertNotIn("absent", result.facts["metrics"])

    def test_empty_and_sales_are_authoritative(self):
        self.assertEqual(self.report().facts["metrics"]["attended_employees"], 0)
        order = Order.objects.create(
            business=self.business,
            number="A-1",
            currency="PHP",
            subtotal=Decimal("123.45"),
            grand_total=Decimal("123.45"),
        )
        Order.objects.filter(pk=order.pk).update(
            placed_at=datetime(2026, 10, 26, 1, tzinfo=dt_timezone.utc)
        )
        self.assertEqual(
            self.report("sales").facts["metrics"]["ordered_sales"], "123.45"
        )

    def test_sales_chart_and_product_rows_are_scoped_saved_facts(self):
        from commerce.models import OrderItem

        own = Order.objects.create(
            business=self.business, number="SAVED-1", currency="PHP",
            subtotal="200.00", grand_total="200.00", payment_status="paid",
        )
        item = OrderItem.objects.create(
            order=own, name="Canvas tote", sku="TOTE-1", quantity=2,
            unit_price="100.00", line_total="200.00",
            offering_snapshot={"private_note": "do not include"},
        )
        other = Business.objects.create(display_name="Other", created_by=self.user)
        foreign = Order.objects.create(
            business=other, number="FOREIGN", currency="PHP", subtotal="900.00", grand_total="900.00",
        )
        cancelled = Order.objects.create(
            business=self.business, number="CANCELLED", currency="PHP", subtotal="400.00", grand_total="400.00", status="cancelled",
        )
        Order.objects.filter(pk__in=[own.pk, foreign.pk, cancelled.pk]).update(
            placed_at=datetime(2026, 10, 26, 1, tzinfo=dt_timezone.utc)
        )
        facts = self.report("sales").facts
        self.assertEqual(facts["metrics"]["items_sold"], 2)
        self.assertEqual(facts["metrics"]["average_order_value"], "200.00")
        self.assertEqual(facts["charts"]["sales"], [{"date": "2026-10-26", "sales": "200.00", "orders": 1}])
        self.assertEqual(facts["charts"]["payments"], [{"label": "paid", "sales": "200.00", "orders": 1}])
        row = facts["tables"]["transactions"]["rows"][0]
        self.assertEqual(row["product"], "Canvas tote")
        self.assertIsNone(row["image_url"])
        self.assertNotIn("private_note", str(facts))
        from catalog.models import Offering
        from .models import BusinessAsset

        offering = Offering.objects.create(
            business=self.business, name="Canvas tote", offering_type="product"
        )
        foreign_image = BusinessAsset.objects.create(
            business=other, title="Foreign image", asset_type="image",
            file="foreign.jpg", mime_type="image/jpeg", size_bytes=10, uploaded_by=self.user,
        )
        own_image = BusinessAsset.objects.create(
            business=self.business, title="Own image", asset_type="image",
            file="canvas.jpg", mime_type="image/jpeg", size_bytes=10, uploaded_by=self.user,
        )
        offering.assets.add(foreign_image, own_image)
        item.offering = offering
        item.name = "Changed later"
        item.save()
        self.assertEqual(row["product"], "Canvas tote")
        next_row = self.report("sales").facts["tables"]["transactions"]["rows"][0]
        self.assertEqual(next_row["image_url"], "/media/canvas.jpg")
        self.assertIsNone(row["image_url"], "Existing snapshots keep the earlier image reference")

    def test_dst_day_uses_business_midnights_not_a_fixed_24_hours(self):
        from datetime import timedelta

        self.business.timezone = "America/New_York"
        self.business.save()
        for instant in [
            datetime(2026, 11, 1, 4, tzinfo=dt_timezone.utc),
            datetime(2026, 11, 2, 4, 59, tzinfo=dt_timezone.utc),
            datetime(2026, 11, 2, 5, tzinfo=dt_timezone.utc),
        ]:
            AttendanceRecord.objects.create(
                business=self.business,
                staff=self.staff,
                clock_in=instant,
                clock_out=instant + timedelta(minutes=1),
            )
        result = resolve_report(
            self.context,
            ReportPlan.parse(
                {
                    "kind": "attendance",
                    "date_from": "2026-11-01",
                    "date_to": "2026-11-01",
                }
            ),
        )
        self.assertEqual(result.facts["tables"]["attendance"]["total"], 2)

    def test_detail_caps_do_not_change_aggregates_or_full_counts(self):
        instant = datetime(2026, 10, 26, 1, tzinfo=dt_timezone.utc)
        AttendanceRecord.objects.bulk_create(
            [
                AttendanceRecord(
                    business=self.business,
                    staff=self.staff,
                    clock_in=instant,
                    clock_out=instant,
                )
                for _ in range(10001)
            ],
            batch_size=1000,
        )
        result = self.report()
        table = result.facts["tables"]["attendance"]
        self.assertEqual(table["total"], 10001)
        self.assertEqual(len(table["rows"]), 100)
        self.assertEqual(table["stored"], 10000)
        self.assertTrue(table["truncated"])
        self.assertEqual(len(result.detail_rows), 10000)
        self.assertEqual(result.facts["metrics"]["attended_employees"], 1)
