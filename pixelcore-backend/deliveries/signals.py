from django.db.models.signals import post_save
from django.dispatch import receiver

from commerce.models import Fulfillment, Order
from .services import ensure_delivery


@receiver(post_save, sender=Order)
def sync_delivery_order(sender, instance, raw=False, **kwargs):
    if not raw:
        ensure_delivery(instance)


@receiver(post_save, sender=Fulfillment)
def sync_delivery_fulfillment(sender, instance, raw=False, **kwargs):
    if not raw and instance.fulfillment_type == "delivery":
        ensure_delivery(instance.order)
