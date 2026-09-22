from django.contrib import admin

from .models import PosSession


@admin.register(PosSession)
class PosSessionAdmin(admin.ModelAdmin):
    list_display = ("station", "business", "revision", "last_order", "updated_at")
    search_fields = ("station__name", "business__display_name", "last_order__number")
    readonly_fields = ("public_id", "cart_snapshot", "revision", "last_checkout_key", "updated_at")
