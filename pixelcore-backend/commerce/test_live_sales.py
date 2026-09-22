import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from businesses.models import AuditEvent, Business, BusinessLocation, BusinessMembership
from catalog.models import Offering, OfferingVariant
from operations.models import InventoryBalance
from .models import Order, ProductRequest


class LiveSalesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('live-owner')
        self.business = Business.objects.create(display_name='Live studio', created_by=self.user, timezone='Asia/Manila')
        BusinessMembership.objects.create(business=self.business, user=self.user, role='owner')
        self.location = BusinessLocation.objects.create(business=self.business, name='Main', code='main')
        self.product = Offering.objects.create(business=self.business, name='Camera', offering_type='physical', status='published', track_inventory=True)
        self.variant = OfferingVariant.objects.create(offering=self.product, name='Black', price='100')
        self.balance = InventoryBalance.objects.create(business=self.business, variant=self.variant, location=self.location, on_hand=10, reserved=1)
        self.client = APIClient(); self.client.force_authenticate(self.user)
        self.base = f'/api/businesses/{self.business.public_id}/'

    def request_record(self, **values):
        today = timezone.now().astimezone(ZoneInfo('Asia/Manila')).date()
        return ProductRequest.objects.create(business=self.business, offering=self.product, variant=self.variant, location=self.location,
            kind='rental', quantity=1, first_name='Alex', email='alex@example.com', phone='+639171234567',
            snapshot={'name': 'Camera', 'variant': 'Black'}, idempotency_digest=uuid.uuid4().hex, payload_digest='test',
            **{'starts_on': today - timedelta(days=4), 'ends_on': today - timedelta(days=1), 'status': 'collected', **values})

    def order(self, **values):
        return Order.objects.create(business=self.business, number=uuid.uuid4().hex, currency='PHP', subtotal=100, grand_total=100,
                                    **{'status': 'confirmed', 'payment_status': 'paid', **values})

    def test_paid_series_uses_all_rows_and_excludes_unpaid(self):
        for _ in range(25): self.order()
        self.order(payment_status='unpaid')
        self.order(status='cancelled')
        self.order(payment_status='partially_refunded')
        response = self.client.get(self.base + 'live-sales/?days=7')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Decimal(response.data['sales']['paid_order_value']), Decimal('2500'))
        self.assertEqual(response.data['sales']['paid_orders'], 25)
        self.assertEqual(len(response.data['series']), 7)
        self.assertEqual(sum(Decimal(row['value']) for row in response.data['series']), Decimal('2500'))

    def test_orders_and_requests_are_paginated_with_full_counts(self):
        for _ in range(23):
            self.order(); self.request_record(status='pending')
        orders = self.client.get(self.base + 'orders/?page=2')
        requests = self.client.get(self.base + 'product-requests/?page=2')
        self.assertEqual(orders.data['count'], 23); self.assertEqual(len(orders.data['results']), 3)
        self.assertEqual(requests.data['summary']['pending'], 23); self.assertEqual(len(requests.data['results']), 3)
        self.assertEqual(self.client.get(self.base + 'product-requests/?search=nobody').data['count'], 0)

    def test_overdue_is_local_day_and_excludes_returned(self):
        self.request_record(ends_on='2026-09-06')
        self.request_record(status='returned', ends_on='2026-09-01')
        self.request_record(ends_on='2026-09-07')
        # It is already September 7 in Manila, even though UTC is still September 6.
        with patch('commerce.live_sales.timezone.now', return_value=datetime(2026, 9, 6, 17, tzinfo=dt_timezone.utc)):
            response = self.client.get(self.base + 'product-requests/?scope=overdue')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['attention']['days'], 1)
        self.assertEqual(response.data['summary']['returned'], 1)
        self.assertEqual(response.data['summary']['due_today'], 1)

    def test_extend_and_followup_are_audited_without_releasing_stock(self):
        item = self.request_record(balance=self.balance, stock_held=True)
        url = self.base + f'product-requests/{item.public_id}/transition/'
        response = self.client.post(url, {'action': 'extend', 'note': 'Customer agreed by phone', 'ends_on': str(timezone.localdate() + timedelta(days=5)), 'expected_updated_at': item.updated_at.isoformat()}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.balance.refresh_from_db(); self.assertEqual(self.balance.reserved, 1)
        self.assertTrue(AuditEvent.objects.filter(resource_id=str(item.public_id), action='product_request.extend').exists())
        stale = self.client.post(url, {'action': 'return', 'expected_updated_at': item.updated_at.isoformat()}, format='json')
        self.assertEqual(stale.status_code, 409)
        item.refresh_from_db()
        follow_up = self.client.post(url, {'action': 'follow_up', 'note': 'Confirmed pickup time', 'expected_updated_at': item.updated_at.isoformat()}, format='json')
        self.assertEqual(follow_up.status_code, 200)
        item.refresh_from_db(); self.assertEqual(item.status, 'collected')

    def test_staff_cannot_see_or_mutate_rental_requests(self):
        staff = get_user_model().objects.create_user('live-staff')
        BusinessMembership.objects.create(business=self.business, user=staff, role='staff')
        item = self.request_record()
        self.client.force_authenticate(staff)
        self.assertIsNone(self.client.get(self.base + 'live-sales/').data['requests'])
        self.assertEqual(self.client.get(self.base + 'product-requests/').status_code, 404)
        self.assertEqual(self.client.post(self.base + f'product-requests/{item.public_id}/transition/', {'action': 'follow_up', 'note': 'No access'}, format='json').status_code, 404)

    def test_another_business_is_not_visible(self):
        outsider = get_user_model().objects.create_user('other-owner')
        self.client.force_authenticate(outsider)
        self.assertEqual(self.client.get(self.base + 'live-sales/').status_code, 404)
        self.assertEqual(self.client.get(self.base + 'orders/').status_code, 404)
