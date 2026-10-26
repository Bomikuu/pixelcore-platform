import hashlib
import io
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Sum
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from businesses.demo.common import FIXTURE, money
from businesses.demo.importer import import_month
from businesses.models import Business, BusinessAsset, BusinessMembership
from catalog.models import Offering, OfferingMedia, OfferingVariant
from commerce.models import Customer, Order, PaymentAttempt, Refund
from content.models import PageRevision
from displays.models import DisplayPublication
from operations.models import InventoryBalance, Invoice, PurchaseOrder
from scheduling.models import Booking, StaffProfile, VenueEvent
from workforce.models import AttendanceRecord


NOW = datetime(2026, 10, 23, 12, tzinfo=ZoneInfo("Asia/Manila"))


@override_settings(DEBUG=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MonthlyDemoTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media = TemporaryDirectory()
        cls.media_settings = override_settings(MEDIA_ROOT=cls.media.name)
        cls.media_settings.enable()
        cls.clock = patch("businesses.demo.common.timezone.now", return_value=NOW)
        cls.clock.start()
        try:
            super().setUpClass()
        except Exception:
            cls.clock.stop()
            cls.media_settings.disable()
            cls.media.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            super().tearDownClass()
        finally:
            cls.clock.stop()
            cls.media_settings.disable()
            cls.media.cleanup()

    @classmethod
    def setUpTestData(cls):
        ctx = import_month("2026-10")
        cls.business, cls.owner = ctx.business, ctx.owner

    def counts(self):
        return {m._meta.label: m.objects.count() for m in apps.get_models()}

    def media_files(self):
        return {str(p.relative_to(self.media.name)) for p in Path(self.media.name).rglob("*") if p.is_file()}

    def test_fixture_populates_connected_surfaces(self):
        self.assertEqual(Order.objects.filter(business=self.business).count(), 120)
        self.assertEqual(Booking.objects.filter(business=self.business).count(), 40)
        self.assertEqual(Customer.objects.filter(business=self.business).count(), 24)
        self.assertEqual(StaffProfile.objects.filter(business=self.business).count(), 8)
        self.assertEqual(Offering.objects.filter(business=self.business, offering_type="physical").count(), 6)
        self.assertEqual(OfferingVariant.objects.filter(offering__business=self.business).count(), 11)
        self.assertEqual(PurchaseOrder.objects.filter(business=self.business).count(), 8)
        self.assertEqual(Invoice.objects.filter(business=self.business).count(), 12)
        self.assertEqual(VenueEvent.objects.filter(business=self.business).count(), 4)
        self.assertTrue(self.business.attendance_records.exists())
        self.assertTrue(self.business.site.pages.get(slug="home").published_revision_id)
        self.assertEqual(DisplayPublication.objects.filter(business=self.business, is_published=True).count(), 2)

    def test_repeat_import_preserves_identifiers_passwords_revisions_and_files(self):
        expected_counts, expected_files = self.counts(), self.media_files()
        order_ids = set(self.business.orders.values_list("public_id", flat=True))
        self.owner.set_password("ChangedDemoPassword-123!")
        self.owner.save(update_fields=["password"])
        import_month("2026-10")
        self.assertEqual(self.counts(), expected_counts)
        self.assertEqual(self.media_files(), expected_files)
        self.assertEqual(set(self.business.orders.values_list("public_id", flat=True)), order_ids)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("ChangedDemoPassword-123!"))
        self.assertEqual(PageRevision.objects.count(), 1)

    def test_financial_totals_and_payment_allocations_reconcile(self):
        for order in self.business.orders.prefetch_related("items"):
            self.assertEqual(sum((line.line_total for line in order.items.all()), Decimal(0)), order.subtotal)
            self.assertEqual(order.tax_total, money(order.subtotal * Decimal("0.12")))
            self.assertEqual(order.grand_total, order.subtotal + order.tax_total + order.shipping_total - order.discount_total)
        for invoice in self.business.invoices.all():
            self.assertEqual(sum((line.line_total for line in invoice.lines.all()), Decimal(0)), invoice.subtotal)
            self.assertEqual(invoice.grand_total, invoice.subtotal + invoice.tax_total)
            allocated = invoice.payment_allocations.aggregate(total=Sum("amount"))["total"] or Decimal(0)
            self.assertEqual(allocated, invoice.amount_paid)
            self.assertGreaterEqual(invoice.balance_due, 0)
        for refund in Refund.objects.select_related("payment_attempt"):
            self.assertEqual(refund.amount, refund.payment_attempt.amount)
            self.assertEqual(refund.payment_attempt.order.payment_status, "refunded")

    def test_inventory_matches_ledger_and_reservations(self):
        for balance in InventoryBalance.objects.filter(business=self.business):
            ledger = balance.movements.aggregate(total=Sum("quantity_delta"))["total"] or Decimal(0)
            reserved = balance.reservations.filter(status="active").aggregate(total=Sum("quantity"))["total"] or Decimal(0)
            self.assertEqual(balance.on_hand, ledger)
            self.assertEqual(balance.reserved, reserved)
            self.assertGreaterEqual(balance.available, 0)
        self.assertTrue(any(balance.available <= balance.low_stock_threshold for balance in InventoryBalance.objects.filter(business=self.business)))

    def test_history_is_in_month_and_future_bookings_are_not_completed(self):
        for placed_at in self.business.orders.values_list("placed_at", flat=True):
            self.assertEqual(timezone.localtime(placed_at, NOW.tzinfo).strftime("%Y-%m"), "2026-10")
            self.assertLessEqual(placed_at, NOW)
        self.assertTrue(self.business.bookings.filter(starts_at__gt=NOW, status__in=["confirmed", "pending"]).exists())
        self.assertFalse(self.business.bookings.filter(ends_at__gt=NOW, status="completed").exists())
        bookings = list(self.business.bookings.exclude(status__in=["cancelled", "no_show"]).order_by("starts_at"))
        for i, first in enumerate(bookings):
            self.assertEqual(first.event.business_id, self.business.pk)
            self.assertEqual(first.customer.business_id, self.business.pk)
            for second in bookings[i + 1:]:
                if first.staff_id == second.staff_id:
                    self.assertFalse(first.starts_at < second.ends_at and second.starts_at < first.ends_at)
        for record in AttendanceRecord.objects.filter(business=self.business):
            self.assertLessEqual(record.scheduled_start, NOW)
            self.assertLess(record.scheduled_start.weekday(), 5)
            if record.clock_out:
                self.assertLessEqual(record.clock_out, NOW)

    def test_images_are_bundled_valid_and_resolve_from_catalog_and_site(self):
        assets = BusinessAsset.objects.filter(business=self.business)
        self.assertEqual(assets.count(), 8)
        for asset in assets:
            with asset.file.open("rb") as handle:
                payload = handle.read()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), asset.metadata["sha256"])
            with Image.open(io.BytesIO(payload)) as image:
                self.assertEqual(image.format, "PNG")
                image.verify()
        self.assertEqual(OfferingMedia.objects.filter(business=self.business, role="cover").count(), 9)
        for product in self.business.offerings.filter(offering_type="physical"):
            self.assertTrue(product.assets.get().file.storage.exists(product.assets.get().file.name))
        self.assertTrue(self.business.cover_image.storage.exists(self.business.cover_image.name))

    def test_import_does_not_send_email_payments_or_calendar_requests(self):
        with patch("django.core.mail.send_mail") as mail, patch("requests.sessions.Session.request") as network, patch("celery.app.task.Task.delay") as task:
            import_month("2026-10")
        mail.assert_not_called()
        network.assert_not_called()
        task.assert_not_called()

    def test_published_samples_are_readable_through_public_apis(self):
        client = APIClient()
        for url in [f"/api/public/{self.business.slug}/site/",
                    f"/api/public/{self.business.slug}/storefront/products/",
                    f"/api/public/{self.business.slug}/storefront/products/transit-runner/",
                    *[f"/api/public/displays/{display.share_key}/" for display in self.business.display_publications.all()]]:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, 200, response.content[:300])

    def test_existing_business_is_never_adopted_or_modified(self):
        real = Business.objects.create(slug="existing-real-business", display_name="Keep this business", created_by=self.owner)
        before = self.counts()
        with self.assertRaisesMessage(CommandError, "not managed"):
            import_month("2026-10", slug=real.slug)
        real.refresh_from_db()
        self.assertEqual(real.display_name, "Keep this business")
        self.assertEqual(self.counts(), before)

    def test_attach_to_existing_account_keeps_its_password_and_profile(self):
        user = get_user_model().objects.create_user(username="existing-owner", email="existing-owner@example.test", password="Existing-Password-123!")
        original_hash = user.password
        ctx = import_month("2026-10", slug="attached-demo", owner_email=user.email)
        user.refresh_from_db()
        self.assertEqual(user.password, original_hash)
        self.assertEqual(ctx.business.created_by_id, user.pk)
        self.assertTrue(BusinessMembership.objects.filter(business=ctx.business, user=user, role="owner").exists())
        self.assertFalse(hasattr(user, "account_profile"))
        # Both isolated tenants retain their own records and media.
        self.assertEqual(self.business.orders.count(), 120)
        self.assertEqual(ctx.business.orders.count(), 120)

    def test_past_leap_month_and_second_month_do_not_duplicate_shared_catalog(self):
        import_month("2024-02")
        self.assertEqual(self.business.orders.count(), 240)
        self.assertEqual(self.business.offerings.count(), 9)
        self.assertEqual(self.business.staff_profiles.count(), 8)
        february = self.business.bookings.filter(starts_at__year=2024, starts_at__month=2)
        self.assertEqual(february.count(), 40)
        self.assertTrue(all(booking.starts_at.day <= 29 for booking in february))
        self.assertFalse(february.filter(status__in=["pending", "confirmed"]).exists())
        self.test_inventory_matches_ledger_and_reservations()

    def test_invalid_months_and_production_are_rejected_without_writes(self):
        before = self.counts()
        for month in ("2026-13", "not-a-month", "0000-01", "2027-01"):
            with self.subTest(month=month), self.assertRaises(CommandError):
                import_month(month)
        with override_settings(DEBUG=False), self.assertRaisesMessage(CommandError, "DEBUG"):
            import_month("2026-10")
        self.assertEqual(self.counts(), before)

    def test_invalid_fixture_is_rejected_before_database_or_media_changes(self):
        data = json.loads(FIXTURE.read_text())
        data["orders"][0]["items"][0]["variant"] = "missing-variant"
        before, files = self.counts(), self.media_files()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "dataset.json"
            path.write_text(json.dumps(data))
            (Path(folder) / "images").symlink_to(FIXTURE.parent / "images", target_is_directory=True)
            with self.assertRaisesMessage(CommandError, "Unknown variant"):
                import_month("2026-10", fixture=path)
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.media_files(), files)

    def test_failed_import_rolls_back_new_rows_and_only_its_new_media(self):
        before, files = self.counts(), self.media_files()
        with patch("businesses.demo.importer.publish_demo", side_effect=RuntimeError("simulated failure")):
            with self.assertRaisesMessage(RuntimeError, "simulated failure"):
                import_month("2026-10", slug="rollback-demo", owner_email=self.owner.email)
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.media_files(), files)

    def test_management_command_uses_fixture_and_reports_access(self):
        output = io.StringIO()
        call_command("seed_month_demo", month="2026-10", stdout=output)
        self.assertIn("2026-10", output.getvalue())
        self.assertIn("monthly.demo@example.test", output.getvalue())
        self.assertIn("Orders: 120", output.getvalue())

    def test_media_only_repairs_separate_storage_without_refreshing_activity(self):
        # A copied database can contain valid asset names while Docker's named
        # media volume is empty and the host's media directory contains the files.
        before_counts = self.counts()
        before_activity = list(self.business.orders.order_by("pk").values())
        before_password = get_user_model().objects.get(pk=self.owner.pk).password
        with TemporaryDirectory() as docker_media, override_settings(MEDIA_ROOT=docker_media):
            assets = list(BusinessAsset.objects.filter(business=self.business))
            self.assertTrue(all(not asset.file.storage.exists(asset.file.name) for asset in assets))
            output = io.StringIO()
            call_command("seed_month_demo", media_only=True, stdout=output)
            self.assertIn("8 missing files restored", output.getvalue())
            for asset in assets:
                with asset.file.open("rb") as handle:
                    payload = handle.read()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), asset.metadata["sha256"])
            output = io.StringIO()
            call_command("seed_month_demo", media_only=True, stdout=output)
            self.assertIn("0 missing files restored", output.getvalue())
        self.assertEqual(self.counts(), before_counts)
        self.assertEqual(list(self.business.orders.order_by("pk").values()), before_activity)
        self.assertEqual(get_user_model().objects.get(pk=self.owner.pk).password, before_password)
