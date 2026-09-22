from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Order
from .services import digital_delivery_tokens


@shared_task(name="commerce.tasks.send_digital_delivery")
def send_digital_delivery(order_id):
    order = Order.objects.select_related("customer").prefetch_related("items__offering").get(pk=order_id)
    links = digital_delivery_tokens(order)
    if not links or not order.customer or not order.customer.email:
        return 0
    body = "Your protected downloads are ready:\n\n" + "\n".join(
        f"{item['name']}: {settings.PIXELCORE_PUBLIC_API_URL}/public/downloads/?token={item['token']}" for item in links
    ) + "\n\nLinks expire after seven days and allow up to five downloads."
    send_mail(f"Your downloads from {order.business.display_name}", body, None, [order.customer.email])
    return len(links)


@shared_task(name="commerce.tasks.send_pos_receipt")
def send_pos_receipt(order_id, email):
    order = Order.objects.select_related("business").prefetch_related("items").get(pk=order_id)
    lines = "\n".join(f"{item.quantity} x {item.name} — {order.currency} {item.line_total}" for item in order.items.all())
    body = f"Receipt {order.number}\n\n{lines}\n\nTotal: {order.currency} {order.grand_total}\nPayment: {order.get_payment_status_display()}"
    send_mail(f"Receipt {order.number} from {order.business.display_name}", body, None, [email])
    return 1
