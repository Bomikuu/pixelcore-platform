from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from businesses.models import Business, BusinessLocation
from catalog.models import Offering, OfferingVariant
from commerce.models import Customer
from .models import InventoryBalance, Supplier, SupplierProduct
from .serializers import PurchaseOrderSerializer
from .services import adjust_stock, allocate_invoice_payment, create_invoice, receive_purchase_order


class InventoryAndInvoiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner@example.com", password="safe-test-password")
        self.business = Business.objects.create(display_name="North Star Studio", created_by=self.user)
        self.location = BusinessLocation.objects.create(business=self.business, name="Main", code="main", is_primary=True)
        offering = Offering.objects.create(business=self.business, name="Studio kit", offering_type="physical", base_price="100.00", track_inventory=True)
        self.variant = OfferingVariant.objects.create(offering=offering, name="Default", sku="KIT-1", price="100.00")
        self.customer = Customer.objects.create(business=self.business, email="buyer@example.com")

    def test_stock_adjustment_conserves_balance(self):
        balance = InventoryBalance.objects.create(business=self.business, location=self.location, variant=self.variant, on_hand=Decimal("4"), reserved=Decimal("1"))
        movement = adjust_stock(balance, Decimal("3"), "receive", self.user)
        balance.refresh_from_db()
        self.assertEqual(balance.on_hand, Decimal("7"))
        self.assertEqual(movement.quantity_delta, Decimal("3"))

    def test_invoice_tax_and_payment_allocation(self):
        invoice = create_invoice(self.business, self.customer, [{"description": "Studio kit", "quantity": 1, "unit_price": "112.00", "tax_rate": "12"}], {"status": "issued"}, self.user)
        self.assertEqual(invoice.tax_total, Decimal("12.00"))
        allocate_invoice_payment(invoice, Decimal("50.00"), self.user, "BANK-1")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "partially_paid")
        self.assertEqual(invoice.balance_due, Decimal("62.00"))

    def test_purchase_order_connects_supplier_product_and_tracks_receiving(self):
        supplier = Supplier.objects.create(business=self.business, name="Atlas Distribution")
        serializer = PurchaseOrderSerializer(data={
            "supplier_public_id": str(supplier.public_id),
            "location_public_id": str(self.location.public_id),
            "status": "ordered",
            "lines": [{
                "variant_public_id": str(self.variant.public_id),
                "description": "Studio kit carton",
                "quantity_ordered": "2.000",
                "unit_cost": "70.00",
            }],
        }, context={"business": self.business})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        purchase_order = serializer.save(business=self.business)
        self.assertTrue(SupplierProduct.objects.filter(supplier=supplier, variant=self.variant).exists())

        line = purchase_order.lines.get()
        receive_purchase_order(purchase_order, {str(line.public_id): "1"}, self.user)
        purchase_order.refresh_from_db()
        self.assertEqual(purchase_order.status, "partially_received")
        self.assertIsNone(purchase_order.received_at)

        receive_purchase_order(purchase_order, {str(line.public_id): "1"}, self.user)
        purchase_order.refresh_from_db()
        self.assertEqual(purchase_order.status, "received")
        self.assertIsNotNone(purchase_order.received_at)
        balance = InventoryBalance.objects.get(business=self.business, location=self.location, variant=self.variant)
        self.assertEqual(balance.on_hand, Decimal("2"))
