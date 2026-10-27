from django.db import migrations


def backfill(apps, schema_editor):
    Order = apps.get_model("commerce", "Order")
    Delivery = apps.get_model("deliveries", "Delivery")
    Event = apps.get_model("deliveries", "DeliveryEvent")
    ready = set(apps.get_model("commerce", "Fulfillment").objects.filter(fulfillment_type="delivery", status="ready").values_list("order_id", flat=True))
    for order in Order.objects.filter(fulfillment_type="delivery").iterator(chunk_size=500):
        stage = "delivered" if order.status == "fulfilled" else "cancelled" if order.status in {"cancelled", "refunded"} else "ready" if order.pk in ready else "preparing"
        delivery, created = Delivery.objects.get_or_create(order_id=order.pk, defaults={"stage": stage})
        if created:
            Event.objects.create(delivery_id=delivery.pk, stage=stage, message="Delivery recorded")


class Migration(migrations.Migration):
    dependencies = [("deliveries", "0001_initial")]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
