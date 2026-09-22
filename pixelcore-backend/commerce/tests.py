import hashlib
import hmac
import json
import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from businesses.google_calendar import encrypt_token
from businesses.models import AuditEvent, Business, BusinessDevice, BusinessMembership, DeviceLink
from businesses.services import current_device_pairing_code, issue_device_pairing_code, pair_device
from catalog.models import Offering
from displays.models import DisplayPublication
from scheduling.models import StaffProfile
from workforce.services import issue_staff_pin
from .models import CartItem, Customer, CustomerAddress, PaymentAttempt, PaymentConnection, PosSession, WebhookEvent
from .services import create_cart, create_order_from_cart, process_paymongo_webhook


class PublicCommerceFlowTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("shopper@example.com", email="shopper@example.com", password="safe-test-password")
        self.owner = get_user_model().objects.create_user("shop-owner@example.com", email="shop-owner@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="Commerce Studio", status="active", created_by=self.owner)
        self.offering = Offering.objects.create(business=self.business, name="Canvas tote", offering_type="physical", fulfillment_type="pickup", base_price="450.00", status="published")
        self.cart, self.token = create_cart(self.business)
        self.item = CartItem.objects.create(cart=self.cart, offering=self.offering, quantity=1, unit_price=Decimal("450.00"), tax_rate=Decimal("0"), selection_key="")

    def test_cart_item_patch_reprices_on_server(self):
        response = self.client.patch(f"/api/public/{self.business.slug}/carts/{self.cart.public_id}/items/{self.item.public_id}/", {"quantity": 3}, format="json", HTTP_X_CART_TOKEN=self.token)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["items"][0]["quantity"], 3)
        self.assertEqual(Decimal(response.data["totals"]["grand_total"]), Decimal("1350.00"))

    def test_order_confirmation_requires_original_cart_token(self):
        order = create_order_from_cart(self.cart, {"email": "buyer@example.com", "first_name": "Buyer", "last_name": "One", "payment_method": "manual", "fulfillment_type": "pickup", "shipping_total": 0})
        path = f"/api/public/{self.business.slug}/orders/{order.public_id}/"
        self.assertEqual(self.client.get(path, HTTP_X_CART_TOKEN="wrong").status_code, 403)
        response = self.client.get(path, HTTP_X_CART_TOKEN=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["number"], order.number)
        self.assertNotIn("offering_snapshot", response.data["items"][0])

    def test_guest_wishlist_merge_is_idempotent(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
        path = f"/api/public/{self.business.slug}/portal/saved/merge/"
        payload = {"offering_public_ids": [str(self.offering.public_id)]}
        self.assertEqual(self.client.post(path, payload, format="json").status_code, 200)
        response = self.client.post(path, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_customer_can_update_profile_and_manage_only_their_addresses(self):
        other_user = get_user_model().objects.create_user(
            "other-shopper@example.com",
            email="other-shopper@example.com",
            password="safe-test-password",
        )
        other_customer = Customer.objects.create(
            business=self.business,
            user=other_user,
            email=other_user.email,
        )
        other_address = CustomerAddress.objects.create(
            customer=other_customer,
            recipient_name="Other Shopper",
            line1="Private address",
            city="Cebu City",
            region="Cebu",
            country="PH",
            is_default=True,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
        portal_path = f"/api/public/{self.business.slug}/portal/"

        profile_response = self.client.patch(
            portal_path,
            {
                "first_name": "Sam",
                "last_name": "Rivera",
                "phone": "+63 917 555 0101",
                "accepts_marketing": True,
            },
            format="json",
        )
        self.assertEqual(profile_response.status_code, 200, profile_response.data)
        self.assertEqual(profile_response.data["first_name"], "Sam")

        address_response = self.client.post(
            f"{portal_path}addresses/",
            {
                "label": "Home",
                "recipient_name": "Sam Rivera",
                "line1": "123 Market Street",
                "city": "Makati",
                "region": "Metro Manila",
                "postal_code": "1200",
                "country": "ph",
                "phone": "+63 917 555 0101",
            },
            format="json",
        )
        self.assertEqual(address_response.status_code, 201, address_response.data)
        self.assertTrue(address_response.data["is_default"])
        self.assertEqual(address_response.data["country"], "PH")

        forbidden_response = self.client.patch(
            f"{portal_path}addresses/{other_address.public_id}/",
            {"label": "Changed"},
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, 404)
        other_address.refresh_from_db()
        self.assertEqual(other_address.label, "")


class CheckoutAndWebhookTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("owner@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="North Star Studio", created_by=user)
        self.offering = Offering.objects.create(business=self.business, name="Digital guide", offering_type="digital", fulfillment_type="digital", base_price="100.00", tax_rate="12")

    def test_checkout_uses_server_side_cart_prices_and_locks_currency(self):
        cart, _ = create_cart(self.business)
        CartItem.objects.create(cart=cart, offering=self.offering, quantity=2, unit_price=Decimal("100.00"), tax_rate=Decimal("12"))
        order = create_order_from_cart(cart, {"email": "buyer@example.com", "payment_method": "manual", "fulfillment_type": "digital", "shipping_total": 0})

        self.assertEqual(order.subtotal, Decimal("200.00"))
        self.assertEqual(order.grand_total, Decimal("200.00"))
        self.business.refresh_from_db()
        self.assertIsNotNone(self.business.currency_locked_at)

    def test_webhook_is_signed_replay_safe_and_idempotent(self):
        cart, _ = create_cart(self.business)
        CartItem.objects.create(cart=cart, offering=self.offering, quantity=1, unit_price=Decimal("100.00"), tax_rate=Decimal("0"))
        order = create_order_from_cart(cart, {"email": "buyer@example.com", "payment_method": "paymongo", "fulfillment_type": "digital", "shipping_total": 0})
        PaymentAttempt.objects.create(business=self.business, order=order, provider="paymongo", provider_reference="cs_1", amount=order.grand_total, currency=order.currency, idempotency_key="checkout-1", status="pending")
        secret = "webhook-secret"
        PaymentConnection.objects.create(business=self.business, provider="paymongo", encrypted_webhook_secret=encrypt_token(secret), is_active=True)
        payload = {"data": {"id": "evt_1", "attributes": {"type": "checkout_session.payment.paid", "data": {"id": "cs_1", "attributes": {"reference_number": order.number}}}}}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        timestamp = str(int(time.time()))
        signature = hmac.new(secret.encode(), timestamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        header = f"t={timestamp},te={signature}"

        process_paymongo_webhook(self.business, raw, header)
        self.assertIsNone(process_paymongo_webhook(self.business, raw, header))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(WebhookEvent.objects.count(), 1)


class PosDeviceSessionTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("pos-owner@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="Counter Studio", created_by=self.user)
        self.membership = BusinessMembership.objects.create(business=self.business, user=self.user, role="owner")
        self.manager = StaffProfile.objects.create(business=self.business, membership=self.membership, display_name="Morgan Manager", employment_status="active")
        self.manager_pin = issue_staff_pin(self.manager)
        self.offering = Offering.objects.create(business=self.business, name="Counter item", offering_type="physical", fulfillment_type="pickup", base_price="125.00", status="published")
        self.station = BusinessDevice.objects.create(business=self.business, name="Counter one", device_type="pos", created_by=self.user)
        self.display = BusinessDevice.objects.create(business=self.business, name="Front display", device_type="customer_display", created_by=self.user)
        self.kitchen = BusinessDevice.objects.create(business=self.business, name="Prep screen", device_type="kitchen_display", created_by=self.user)
        self.dispatch = BusinessDevice.objects.create(business=self.business, name="Delivery screen", device_type="dispatch_display", created_by=self.user)
        DeviceLink.objects.create(business=self.business, source_device=self.station, target_device=self.display, created_by=self.user)
        _, self.station_token = pair_device(issue_device_pairing_code(self.station))
        _, self.display_token = pair_device(issue_device_pairing_code(self.display))
        _, self.kitchen_token = pair_device(issue_device_pairing_code(self.kitchen))
        _, self.dispatch_token = pair_device(issue_device_pairing_code(self.dispatch))

    def test_pairing_code_remains_retrievable_until_used(self):
        spare = BusinessDevice.objects.create(business=self.business, name="Spare counter", device_type="pos", created_by=self.user)
        code = issue_device_pairing_code(spare)
        spare.refresh_from_db()
        self.assertEqual(current_device_pairing_code(spare), code)
        pair_device(code)
        spare.refresh_from_db()
        self.assertEqual(current_device_pairing_code(spare), "")

    def test_session_is_server_priced_and_customer_display_is_station_scoped(self):
        response = self.client.put("/api/devices/pos/session/", {"if_revision": 0, "items": [{"offering_public_id": str(self.offering.public_id), "quantity": 2}]}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart"]["grand_total"], "250.00")
        display = self.client.get("/api/public/devices/customer-display/", HTTP_X_DEVICE_TOKEN=self.display_token)
        self.assertTrue(display.data["linked"])
        self.assertEqual(display.data["session"]["station_public_id"], str(self.station.public_id))
        self.assertEqual(display.data["session"]["cart"]["grand_total"], "250.00")

    def test_customer_display_only_returns_its_selected_promotions(self):
        selected = DisplayPublication.objects.create(
            business=self.business,
            name="Front counter offer",
            kind="promotion",
            settings={"heading": "Today only", "message": "Ask about the counter bundle."},
            is_published=True,
            created_by=self.user,
        )
        DisplayPublication.objects.create(
            business=self.business,
            name="Unrelated announcement",
            kind="information",
            settings={"heading": "Staff briefing"},
            is_published=True,
            created_by=self.user,
        )
        self.display.configuration = {
            "ad_content_mode": "selected",
            "promotion_display_ids": [str(selected.public_id)],
            "ad_rotation_seconds": 8,
        }
        self.display.save(update_fields=["configuration", "updated_at"])

        response = self.client.get("/api/public/devices/customer-display/", HTTP_X_DEVICE_TOKEN=self.display_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["public_id"] for item in response.data["advertisements"]], [str(selected.public_id)])
        self.assertEqual(response.data["advertisements"][0]["heading"], "Today only")
        self.assertEqual(response.data["display_preferences"]["rotation_seconds"], 8)

    def test_stale_revision_conflicts_and_duplicate_checkout_is_idempotent(self):
        payload = {"items": [{"offering_public_id": str(self.offering.public_id), "quantity": 1}]}
        self.client.put("/api/devices/pos/session/", {"if_revision": 0, **payload}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        stale = self.client.put("/api/devices/pos/session/", {"if_revision": 0, **payload}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(stale.status_code, 409)
        checkout = {**payload, "payment_method": "manual", "payment_status": "paid", "fulfillment_type": "pickup"}
        first = self.client.post("/api/devices/pos/checkout/", checkout, format="json", HTTP_X_DEVICE_TOKEN=self.station_token, HTTP_IDEMPOTENCY_KEY="sale-1")
        second = self.client.post("/api/devices/pos/checkout/", checkout, format="json", HTTP_X_DEVICE_TOKEN=self.station_token, HTTP_IDEMPOTENCY_KEY="sale-1")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["public_id"], second.data["public_id"])
        self.assertEqual(PosSession.objects.get(station=self.station).last_order.number, first.data["number"])

    def test_preparation_and_delivery_screens_have_separate_actionable_queues(self):
        item = {"offering_public_id": str(self.offering.public_id), "quantity": 1}
        pickup = self.client.post(
            "/api/devices/pos/checkout/",
            {"items": [item], "payment_method": "manual", "payment_status": "paid", "fulfillment_type": "pickup"},
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_IDEMPOTENCY_KEY="pickup-order",
        )
        delivery = self.client.post(
            "/api/devices/pos/checkout/",
            {
                "items": [item],
                "payment_method": "manual",
                "payment_status": "unpaid",
                "fulfillment_type": "delivery",
                "shipping_address": {"line1": "18 Market Street", "city": "Makati", "region": "Metro Manila"},
            },
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_IDEMPOTENCY_KEY="delivery-order",
        )
        self.assertEqual(pickup.status_code, 201)
        self.assertEqual(delivery.status_code, 201)
        self.assertEqual(delivery.data["shipping_snapshot"]["city"], "Makati")

        prep_queue = self.client.get("/api/devices/orders/queue/", HTTP_X_DEVICE_TOKEN=self.kitchen_token)
        delivery_queue = self.client.get("/api/devices/orders/queue/", HTTP_X_DEVICE_TOKEN=self.dispatch_token)
        self.assertEqual({item["public_id"] for item in prep_queue.data["orders"]}, {pickup.data["public_id"], delivery.data["public_id"]})
        self.assertEqual([item["public_id"] for item in delivery_queue.data["orders"]], [delivery.data["public_id"]])

        counter_queue = self.client.get("/api/devices/orders/queue/", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(counter_queue.status_code, 200)
        self.assertEqual(counter_queue.data["queue_type"], "delivery_overview")
        self.assertEqual([item["public_id"] for item in counter_queue.data["orders"]], [delivery.data["public_id"]])

        payment = self.client.post(
            f"/api/devices/orders/{delivery.data['public_id']}/payment/",
            {"payment_method": "cash"},
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_IDEMPOTENCY_KEY="delivery-payment-1",
        )
        self.assertEqual(payment.status_code, 200)
        self.assertEqual(payment.data["payment_status"], "paid")
        self.assertTrue(PaymentAttempt.objects.filter(order__public_id=delivery.data["public_id"], provider="pos_cash", status="paid").exists())

        for action in ("start", "ready", "complete"):
            response = self.client.patch(
                f"/api/devices/orders/{pickup.data['public_id']}/status/",
                {"action": action},
                format="json",
                HTTP_X_DEVICE_TOKEN=self.kitchen_token,
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "fulfilled")

        self.client.patch(f"/api/devices/orders/{delivery.data['public_id']}/status/", {"action": "start"}, format="json", HTTP_X_DEVICE_TOKEN=self.dispatch_token)
        self.client.patch(f"/api/devices/orders/{delivery.data['public_id']}/status/", {"action": "ready"}, format="json", HTTP_X_DEVICE_TOKEN=self.dispatch_token)
        completed = self.client.patch(f"/api/devices/orders/{delivery.data['public_id']}/status/", {"action": "complete"}, format="json", HTTP_X_DEVICE_TOKEN=self.dispatch_token)
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data["status"], "fulfilled")

    def test_strict_register_requires_single_revision_manager_approval_for_voids(self):
        self.station.configuration = {"strict_mode": True}
        self.station.save(update_fields=["configuration", "updated_at"])
        item = {"offering_public_id": str(self.offering.public_id), "quantity": 2}
        opened = self.client.put("/api/devices/pos/session/", {"if_revision": 0, "items": [item]}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(opened.status_code, 200)
        self.assertTrue(self.client.get("/api/devices/pos/session/", HTTP_X_DEVICE_TOKEN=self.station_token).data["station_controls"]["strict_mode"])

        blocked = self.client.put("/api/devices/pos/session/", {"if_revision": 1, "items": [{**item, "quantity": 1}]}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.data["error"]["code"], "POS_AUTHORIZATION_REQUIRED")

        denied = self.client.post("/api/devices/pos/authorize/", {"action": "void_items", "pin": "000000"}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(denied.status_code, 403)
        approved = self.client.post("/api/devices/pos/authorize/", {"action": "void_items", "pin": self.manager_pin}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(approved.status_code, 200)
        reduced = self.client.put(
            "/api/devices/pos/session/",
            {"if_revision": 1, "items": [{**item, "quantity": 1}]},
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_X_POS_AUTHORIZATION=approved.data["authorization_token"],
        )
        self.assertEqual(reduced.status_code, 200)
        replayed = self.client.put(
            "/api/devices/pos/session/",
            {"if_revision": 2, "items": []},
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_X_POS_AUTHORIZATION=approved.data["authorization_token"],
        )
        self.assertEqual(replayed.status_code, 403)
        self.assertTrue(AuditEvent.objects.filter(business=self.business, action="pos.authorization.approved").exists())

    def test_hold_resume_void_and_station_transaction_controls(self):
        item = {"offering_public_id": str(self.offering.public_id), "quantity": 1, "note": "Gift wrap"}
        opened = self.client.put("/api/devices/pos/session/", {"if_revision": 0, "items": [item]}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(opened.status_code, 200)
        self.assertEqual(opened.data["cart"]["items"][0]["note"], "Gift wrap")

        held = self.client.post("/api/devices/pos/holds/", {"label": "Customer 12"}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(held.status_code, 201)
        self.assertEqual(held.data["cart"]["items"], [])
        hold_id = held.data["held_sales"][0]["public_id"]
        resumed = self.client.post(f"/api/devices/pos/holds/{hold_id}/resume/", format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual(resumed.status_code, 200)
        self.assertEqual(resumed.data["cart"]["items"][0]["note"], "Gift wrap")

        sale = self.client.post(
            "/api/devices/pos/checkout/",
            {"items": [item], "payment_method": "cash", "payment_status": "paid", "fulfillment_type": "pickup"},
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_IDEMPOTENCY_KEY="cash-sale-controls",
        )
        self.assertEqual(sale.status_code, 201)
        recent = self.client.get("/api/devices/pos/transactions/", HTTP_X_DEVICE_TOKEN=self.station_token)
        self.assertEqual([order["public_id"] for order in recent.data["orders"]], [sale.data["public_id"]])

        approval = self.client.post("/api/devices/pos/authorize/", {"action": "refund", "pin": self.manager_pin}, format="json", HTTP_X_DEVICE_TOKEN=self.station_token)
        refunded = self.client.post(
            f"/api/devices/pos/transactions/{sale.data['public_id']}/refund/",
            {"reason": "Customer returned the item"},
            format="json",
            HTTP_X_DEVICE_TOKEN=self.station_token,
            HTTP_X_POS_AUTHORIZATION=approval.data["authorization_token"],
        )
        self.assertEqual(refunded.status_code, 200)
        self.assertEqual(refunded.data["payment_status"], "refunded")
        self.assertTrue(AuditEvent.objects.filter(action="pos.order.refunded", resource_id=str(sale.data["public_id"])).exists())
