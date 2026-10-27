from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from businesses.models import AccountProfile, Business, BusinessMembership
from commerce.models import Customer, Fulfillment, Order
from commerce.services import create_cart
from .models import Delivery, RiderAccess


class DeliveryAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user("delivery-owner", email="owner@example.test")
        self.rider = User.objects.create_user("delivery-rider", email="rider@example.test")
        self.other = User.objects.create_user("delivery-other", email="other@example.test")
        self.customer_user = User.objects.create_user("delivery-customer", email="customer@example.test")
        self.business = Business.objects.create(display_name="Delivery shop", created_by=self.owner, status="active")
        self.other_business = Business.objects.create(display_name="Other shop", created_by=self.other, status="active")
        BusinessMembership.objects.create(business=self.business, user=self.owner, role="owner")
        BusinessMembership.objects.create(business=self.other_business, user=self.other, role="owner")
        self.membership = BusinessMembership.objects.create(business=self.business, user=self.rider, role="staff")
        self.customer = Customer.objects.create(business=self.business, user=self.customer_user, email=self.customer_user.email)
        self.cart, self.cart_token = create_cart(self.business)
        self.order = Order.objects.create(business=self.business, customer=self.customer, cart=self.cart, number="D-001", status="confirmed", fulfillment_type="delivery", currency="PHP", subtotal=100, grand_total=100, shipping_snapshot={"line1": "1 Test Street", "city": "Manila"}, customer_snapshot={"first_name": "Test", "phone": "123"})
        self.fulfillment = Fulfillment.objects.create(order=self.order, fulfillment_type="delivery", status="ready")
        self.delivery = Delivery.objects.get(order=self.order)
        self.grant = RiderAccess.objects.create(business=self.business, user=self.rider, email=self.rider.email, display_name="Test Rider", kind="employee", status="active")
        self.delivery.rider = self.grant
        self.delivery.save()
        self.owner_path = f"/api/businesses/{self.business.public_id}/deliveries/"
        self.rider_path = f"/api/rider/deliveries/{self.delivery.public_id}/"
        self.customer_path = f"/api/public/{self.business.slug}/orders/{self.order.public_id}/tracking/"
        self.client.force_authenticate(self.owner)

    def change(self, action, **kwargs):
        self.delivery.refresh_from_db()
        return self.client.patch(f"{self.owner_path}{self.delivery.public_id}/", {"action": action, "revision": self.delivery.revision, **kwargs}, format="json")

    def depart(self):
        response = self.change("stage", stage="out_for_delivery")
        self.assertEqual(response.status_code, 200, response.data)
        self.delivery.refresh_from_db()
        self.client.force_authenticate(self.rider)
        response = self.client.patch(self.rider_path, {"revision": self.delivery.revision, "action": "sharing", "sharing": True}, format="json")
        self.assertEqual(response.status_code, 200, response.data)

    def gps(self, **kwargs):
        payload = {"revision": self.delivery.revision, "latitude": 14.6, "longitude": 120.98, "accuracy": 8, "captured_at": timezone.now().isoformat(), **kwargs}
        return self.client.post(self.rider_path + "location/", payload, format="json")

    def test_owner_scope_and_staff_cannot_manage(self):
        response = self.client.get(self.owner_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.owner_path).status_code, 404)
        self.client.force_authenticate(self.rider)
        self.assertEqual(self.client.get(self.owner_path).status_code, 404)

    def test_customer_requires_owner_or_cart_token_and_redacts(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.customer_path).status_code, 403)
        self.client.force_authenticate(self.customer_user)
        response = self.client.get(self.customer_path)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("customer_phone", response.data["delivery"])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.customer_path).status_code, 403)
        self.assertEqual(self.client.get(self.customer_path, HTTP_X_CART_TOKEN=self.cart_token).status_code, 200)

    def test_guest_non_delivery_order_is_not_trackable(self):
        self.order.fulfillment_type = "pickup"
        self.order.save()
        self.order.delivery.delete()
        self.assertEqual(self.client.get(self.customer_path, HTTP_X_CART_TOKEN=self.cart_token).status_code, 404)

    def test_rider_cannot_see_others_deliveries(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/rider/deliveries/").data["results"], [])
        self.assertEqual(self.client.patch(self.rider_path, {"revision": 1, "action": "sharing", "sharing": True}, format="json").status_code, 404)

    def test_employee_suspension_removes_access_and_location(self):
        self.depart()
        self.assertEqual(self.gps().status_code, 200)
        self.membership.status = "suspended"
        self.membership.save()
        self.assertEqual(self.client.get("/api/rider/deliveries/").data["results"], [])
        self.assertEqual(self.gps().status_code, 404)
        self.client.force_authenticate(self.customer_user)
        self.assertIsNone(self.client.get(self.customer_path).data["delivery"]["location"])

    def test_independent_invitation_requires_matching_verified_account(self):
        grant = RiderAccess.objects.create(business=self.business, email=self.other.email, display_name="Independent", kind="independent")
        path = f"/api/rider/access/{grant.public_id}/accept/"
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(path).status_code, 403)
        AccountProfile.objects.update_or_create(user=self.other, defaults={"email_verified_at": timezone.now()})
        self.assertEqual(self.client.post(path).status_code, 200)
        grant.refresh_from_db()
        self.assertEqual(grant.user, self.other)
        self.assertFalse(BusinessMembership.objects.filter(business=self.business, user=self.other).exists())
        self.assertEqual(self.client.get(self.owner_path).status_code, 404)

    def test_independent_rider_home_without_onboarding(self):
        RiderAccess.objects.create(business=self.business, email=self.other.email, display_name="Independent", kind="independent")
        BusinessMembership.objects.filter(user=self.other).delete()
        AccountProfile.objects.update_or_create(user=self.other, defaults={"email_verified_at": timezone.now()})
        self.client.force_authenticate(self.other)
        me = self.client.get("/api/auth/me/").data
        self.assertTrue(me["has_delivery_access"])
        self.assertFalse(me["needs_onboarding"])

    def test_invalid_employee_and_duplicate_grants(self):
        path = f"/api/businesses/{self.business.public_id}/delivery-riders/"
        self.assertEqual(self.client.post(path, {"email": self.other.email, "display_name": "Other", "kind": "employee"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(path, {"email": self.rider.email, "display_name": "Rider", "kind": "employee"}, format="json").status_code, 400)

    def test_no_dispatch_without_active_assignment(self):
        self.delivery.rider = None
        self.delivery.save()
        self.assertEqual(self.change("stage", stage="out_for_delivery").status_code, 400)

    def test_revision_conflict_and_unsupported_transition(self):
        self.assertEqual(self.client.patch(f"{self.owner_path}{self.delivery.public_id}/", {"revision": 999, "action": "stage", "stage": "out_for_delivery"}, format="json").status_code, 409)
        self.assertEqual(self.change("stage", stage="delivered").status_code, 409)

    def test_gps_sharing_permission_and_thirty_second_gate(self):
        self.depart()
        event_count = self.delivery.events.count()
        self.assertTrue(self.gps().data["accepted"])
        response = self.gps(latitude=15)
        self.assertFalse(response.data["accepted"])
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.latitude, 14.6)
        self.assertEqual(self.delivery.events.count(), event_count)  # GPS is not history
        self.client.force_authenticate(self.customer_user)
        self.assertFalse(self.client.get(self.customer_path).data["delivery"]["location"]["stale"])

    def test_invalid_old_future_and_out_of_order_gps(self):
        self.depart()
        for payload in ({"latitude": 91}, {"longitude": -181}, {"accuracy": -1}, {"captured_at": (timezone.now() - timedelta(seconds=121)).isoformat()}, {"captured_at": (timezone.now() + timedelta(seconds=30)).isoformat()}):
            self.assertEqual(self.gps(**payload).status_code, 400, payload)
        now = timezone.now()
        self.assertEqual(self.gps(captured_at=now.isoformat()).status_code, 200)
        self.assertEqual(self.gps(captured_at=(now - timedelta(seconds=1)).isoformat()).status_code, 409)

    def test_stale_marker_and_stop_clears_point(self):
        self.depart()
        self.gps()
        Delivery.objects.filter(pk=self.delivery.pk).update(received_at=timezone.now() - timedelta(seconds=91))
        self.client.force_authenticate(self.customer_user)
        self.assertTrue(self.client.get(self.customer_path).data["delivery"]["location"]["stale"])
        self.client.force_authenticate(self.rider)
        self.client.patch(self.rider_path, {"revision": self.delivery.revision, "action": "sharing", "sharing": False}, format="json")
        self.delivery.refresh_from_db()
        self.assertIsNone(self.delivery.latitude)

    def test_reassignment_clears_position_and_old_revision(self):
        self.depart()
        self.gps()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change("assign", rider_id=None).status_code, 200)
        self.delivery.refresh_from_db()
        self.assertIsNone(self.delivery.latitude)
        self.assertEqual(self.delivery.stage, "ready")
        self.client.force_authenticate(self.rider)
        self.assertEqual(self.gps().status_code, 404)

    def test_revocation_removes_assigned_delivery(self):
        self.depart()
        self.gps()
        self.client.force_authenticate(self.owner)
        path = f"/api/businesses/{self.business.public_id}/delivery-riders/{self.grant.public_id}/"
        self.assertEqual(self.client.delete(path).status_code, 204)
        self.delivery.refresh_from_db()
        self.assertIsNone(self.delivery.latitude)
        self.assertIsNone(self.delivery.rider_id)

    @patch("operations.services.commit_order_stock", side_effect=ValueError("Insufficient stock"))
    def test_completion_rolls_back_when_inventory_commit_fails(self, commit):
        self.depart()
        response = self.client.patch(self.rider_path, {"revision": self.delivery.revision, "action": "stage", "stage": "delivered"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertNotEqual(self.order.status, "fulfilled")
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.stage, "out_for_delivery")

    @patch("operations.services.commit_order_stock")
    def test_completion_commits_order_and_removes_gps(self, commit):
        self.depart()
        self.gps()
        response = self.client.patch(self.rider_path, {"revision": self.delivery.revision, "action": "stage", "stage": "delivered"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        commit.assert_called_once()
        self.order.refresh_from_db()
        self.fulfillment.refresh_from_db()
        self.assertEqual(self.order.status, "fulfilled")
        self.assertEqual(self.fulfillment.status, "fulfilled")
        self.assertIsNone(response.data["location"])

    def test_legacy_order_status_sync_stops_tracking(self):
        self.depart()
        self.gps()
        self.order.status = "cancelled"
        self.order.save()
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.stage, "cancelled")
        self.assertIsNone(self.delivery.latitude)

    def test_destination_pin_validation_and_clear(self):
        self.assertEqual(self.change("destination", latitude=14.6, longitude=120.98).status_code, 200)
        self.assertEqual(self.change("destination", latitude=200, longitude=1).status_code, 400)
        self.assertEqual(self.change("destination", latitude=None, longitude=None).status_code, 200)

    def test_another_point_is_accepted_after_thirty_seconds(self):
        self.depart()
        self.gps(captured_at=(timezone.now() - timedelta(seconds=35)).isoformat())
        Delivery.objects.filter(pk=self.delivery.pk).update(received_at=timezone.now() - timedelta(seconds=31))
        response = self.gps(latitude=14.7)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["accepted"])

    def test_assigning_a_rider_from_another_business_is_denied(self):
        grant = RiderAccess.objects.create(business=self.other_business, user=self.other, email=self.other.email, display_name="Other rider", kind="independent", status="active")
        self.assertEqual(self.change("assign", rider_id=str(grant.public_id)).status_code, 404)

    def test_nonfinite_coordinates_are_rejected(self):
        from .services import coordinates
        from rest_framework.exceptions import ValidationError
        for lat, lng in [(float("nan"), 1), (1, float("inf"))]:
            with self.assertRaises(ValidationError):
                coordinates(lat, lng)

    def test_rider_cannot_cancel_or_assign_a_delivery(self):
        self.client.force_authenticate(self.rider)
        for payload in ({"action": "stage", "stage": "cancelled"}, {"action": "assign", "rider_id": None}):
            response = self.client.patch(self.rider_path, {"revision": self.delivery.revision, **payload}, format="json")
            self.assertEqual(response.status_code, 403)

    def test_customer_payload_never_exposes_invitation_email(self):
        self.client.force_authenticate(self.customer_user)
        response = self.client.get(self.customer_path)
        self.assertNotIn("email", response.data["delivery"]["rider"])
        self.assertNotIn("items", response.data["delivery"])

    def test_owner_can_assign_an_active_employee_rider(self):
        response = self.change("assign", rider_id=str(self.grant.public_id))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["rider"]["public_id"], str(self.grant.public_id))

    def test_independent_rider_can_track_and_complete_only_their_assignment(self):
        grant = RiderAccess.objects.create(business=self.business, email=self.other.email, display_name="Independent", kind="independent")
        AccountProfile.objects.update_or_create(user=self.other, defaults={"email_verified_at": timezone.now()})
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f"/api/rider/access/{grant.public_id}/accept/").status_code, 200)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.change("assign", rider_id=str(grant.public_id)).status_code, 200)
        self.delivery.refresh_from_db()
        self.client.force_authenticate(self.other)
        rows = self.client.get("/api/rider/deliveries/").data["results"]
        self.assertEqual([row["public_id"] for row in rows], [str(self.delivery.public_id)])
        response = self.client.patch(self.rider_path, {"revision": self.delivery.revision, "action": "stage", "stage": "out_for_delivery"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.owner_path).status_code, 404)
        response = self.client.patch(self.rider_path, {"revision": response.data["revision"], "action": "stage", "stage": "delivered"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "fulfilled")
