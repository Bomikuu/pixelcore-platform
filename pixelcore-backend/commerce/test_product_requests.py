import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from businesses.models import Business, BusinessLocation, BusinessMembership
from catalog.models import Offering, OfferingVariant, ProductProfile
from catalog.serializers import PublicOfferingSerializer
from operations.models import InventoryBalance, StockReservation
from .models import Order, ProductRequest, ProductRequestSettings
from .product_requests import release_expired_product_requests


class ProductRequestFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = get_user_model().objects.create_user('requests-owner', password='test-password')
        self.business = Business.objects.create(display_name='Request studio', created_by=self.owner)
        BusinessMembership.objects.create(business=self.business, user=self.owner, role='owner')
        self.location = BusinessLocation.objects.create(business=self.business, name='Main', code='main', is_primary=True)
        self.product = Offering.objects.create(business=self.business, name='Camera', offering_type='physical', status='published', track_inventory=True, base_price='500')
        self.variant = OfferingVariant.objects.create(offering=self.product, name='Black', sku='CAM-1', price='500')
        ProductProfile.objects.create(business=self.business, offering=self.product, reservation_enabled=True, rental_enabled=True, rental_terms='Staff confirms the daily fee.')
        self.settings = ProductRequestSettings.objects.create(business=self.business, reservation_enabled=True, rental_enabled=True, hold_hours=24)
        self.balance = InventoryBalance.objects.create(business=self.business, location=self.location, variant=self.variant, on_hand=2)
        self.client = APIClient()
        self.public_url = f'/api/public/{self.business.slug}/product-requests/'
        self.admin_url = f'/api/businesses/{self.business.public_id}/product-requests/'

    def payload(self, kind='reservation', **updates):
        payload = dict(idempotency_key=str(uuid.uuid4()), offering_public_id=str(self.product.public_id), variant_public_id=str(self.variant.public_id), location_public_id=str(self.location.public_id), kind=kind, quantity=1, first_name='Alex', email='alex@example.com', phone='+639171234567', accepts_terms=True)
        if kind == 'rental':
            payload.update(starts_on=str(timezone.localdate() + timedelta(days=2)), ends_on=str(timezone.localdate() + timedelta(days=4)))
        payload.update(updates)
        return payload

    def create_request(self, kind='reservation', **updates):
        response = self.client.post(self.public_url, self.payload(kind, **updates), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return ProductRequest.objects.get(public_id=response.data['public_id'])

    def transition(self, item, action, **kwargs):
        self.client.force_authenticate(self.owner)
        return self.client.post(f'{self.admin_url}{item.public_id}/transition/', {'action': action, **kwargs}, format='json')

    def test_hold_reserves_stock_and_duplicate_is_idempotent(self):
        body = self.payload()
        first = self.client.post(self.public_url, body, format='json')
        second = self.client.post(self.public_url, body, format='json')
        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(first.data['public_id'], second.data['public_id'])
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.reserved, Decimal('1'))
        self.assertNotIn('email', first.data)
        self.assertNotIn('balance', first.data)
        changed = self.client.post(self.public_url, {**body, 'quantity': 2}, format='json')
        self.assertEqual(changed.status_code, 409)

    def test_overlapping_stock_holds_cannot_oversell(self):
        self.create_request(quantity=2)
        response = self.client.post(self.public_url, self.payload(), format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(ProductRequest.objects.count(), 1)

    def test_expired_hold_releases_once(self):
        item = self.create_request()
        ProductRequest.objects.filter(pk=item.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(release_expired_product_requests(), 1)
        self.assertEqual(release_expired_product_requests(), 0)
        self.balance.refresh_from_db(); item.refresh_from_db()
        self.assertEqual(self.balance.reserved, 0)
        self.assertEqual(item.status, 'expired')

    def test_cancellation_needs_reason_and_releases_hold(self):
        item = self.create_request()
        self.assertEqual(self.transition(item, 'cancel').status_code, 400)
        self.assertEqual(self.transition(item, 'cancel', note='Customer changed plans').status_code, 200)
        self.assertEqual(self.transition(item, 'cancel', note='Duplicate').status_code, 409)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.reserved, 0)

    def test_rental_pending_approval_collection_return(self):
        item = self.create_request('rental')
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.reserved, 0)
        self.assertEqual(self.transition(item, 'approve').status_code, 200)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.reserved, 1)
        self.assertEqual(self.transition(item, 'collect').status_code, 200)
        self.assertEqual(self.transition(item, 'cancel', note='Cannot release an unreturned rental').status_code, 409)
        self.assertEqual(self.transition(item, 'return').status_code, 200)
        self.assertEqual(self.transition(item, 'return').status_code, 409)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.reserved, 0)
        self.assertEqual(self.balance.on_hand, 2)

    def test_rental_approval_rechecks_stock(self):
        rental = self.create_request('rental', quantity=2)
        self.create_request(quantity=1)
        self.assertEqual(self.transition(rental, 'approve').status_code, 409)
        rental.refresh_from_db()
        self.assertEqual(rental.status, 'pending')

    def test_hold_conversion_transfers_stock_to_single_order(self):
        item = self.create_request()
        self.variant.price = Decimal('550'); self.variant.save()
        response = self.transition(item, 'convert')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.transition(item, 'convert').status_code, 409)
        self.balance.refresh_from_db(); item.refresh_from_db()
        self.assertEqual(self.balance.reserved, 1)
        self.assertFalse(item.stock_held)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(item.order.grand_total, Decimal('550'))
        self.assertEqual(item.order.payment_status, 'unpaid')
        self.assertEqual(StockReservation.objects.get(order_item__order=item.order).quantity, Decimal('1'))

    def test_disabled_modes_and_product_eligibility(self):
        self.settings.reservation_enabled = False; self.settings.save()
        response = self.client.post(self.public_url, self.payload(), format='json')
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        options = PublicOfferingSerializer(self.product).data['request_options']
        self.assertFalse(options['reservation_enabled']); self.assertTrue(options['rental_enabled'])
        self.product.track_inventory = False; self.product.save()
        self.assertEqual(self.client.post(self.public_url, self.payload('rental'), format='json').status_code, 400)

    def test_dates_terms_and_cross_tenant_location_are_validated(self):
        self.assertEqual(self.client.post(self.public_url, self.payload('rental', ends_on='2000-01-01'), format='json').status_code, 400)
        self.assertEqual(self.client.post(self.public_url, self.payload(accepts_terms=False), format='json').status_code, 400)
        other = Business.objects.create(display_name='Other', created_by=self.owner)
        location = BusinessLocation.objects.create(business=other, name='Other', code='other')
        self.assertEqual(self.client.post(self.public_url, self.payload(location_public_id=str(location.public_id)), format='json').status_code, 404)

    def test_admin_tenant_and_role_isolation(self):
        item = self.create_request()
        self.assertIn(self.client.get(self.admin_url).status_code, [401, 403])
        outsider = get_user_model().objects.create_user('outsider')
        self.client.force_authenticate(outsider)
        self.assertIn(self.client.get(self.admin_url).status_code, [403, 404])
        BusinessMembership.objects.create(business=self.business, user=outsider, role='staff')
        self.assertIn(self.client.post(f'{self.admin_url}{item.public_id}/transition/', {'action': 'cancel', 'note': 'Denied'}, format='json').status_code, [403, 404])
        item.refresh_from_db(); self.assertEqual(item.status, 'held')

    def test_settings_bounds_and_non_destructive_disable(self):
        item = self.create_request()
        self.client.force_authenticate(self.owner)
        url = f'/api/businesses/{self.business.public_id}/product-request-settings/'
        self.assertEqual(self.client.put(url, {'reservation_enabled': False, 'rental_enabled': True, 'hold_hours': 0}, format='json').status_code, 400)
        self.assertEqual(self.client.put(url, {'reservation_enabled': False, 'rental_enabled': True, 'hold_hours': 48}, format='json').status_code, 200)
        item.refresh_from_db(); self.assertTrue(item.stock_held)
