from celery import shared_task

from .services import release_expired_reservations


@shared_task(name="operations.tasks.release_expired_stock_reservations")
def release_expired_stock_reservations():
    from commerce.product_requests import release_expired_product_requests
    return release_expired_reservations() + release_expired_product_requests()
