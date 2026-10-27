import uuid

from django.conf import settings
from django.db import models


class RiderAccess(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey("businesses.Business", on_delete=models.CASCADE, related_name="delivery_riders")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_access")
    email = models.EmailField()
    display_name = models.CharField(max_length=160)
    kind = models.CharField(max_length=16, choices=[("employee", "Employee"), ("independent", "Independent")])
    status = models.CharField(max_length=16, choices=[("invited", "Invited"), ("active", "Active"), ("revoked", "Revoked")], default="invited")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["business", "email"], name="unique_delivery_rider_email")]
        ordering = ["display_name", "id"]


class Delivery(models.Model):
    STAGES = [(s, s.replace("_", " ").title()) for s in ("preparing", "ready", "out_for_delivery", "delivered", "cancelled")]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.OneToOneField("commerce.Order", on_delete=models.CASCADE, related_name="delivery")
    rider = models.ForeignKey(RiderAccess, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries")
    stage = models.CharField(max_length=24, choices=STAGES, default="preparing", db_index=True)
    revision = models.PositiveIntegerField(default=1)
    destination_latitude = models.FloatField(null=True, blank=True)
    destination_longitude = models.FloatField(null=True, blank=True)
    sharing = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    captured_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-order__placed_at", "id"]


class DeliveryEvent(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name="events")
    stage = models.CharField(max_length=24)
    message = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
