from django.db import migrations


def bootstrap_capabilities(apps, schema_editor):
    Business = apps.get_model("businesses", "Business")
    BusinessCapability = apps.get_model("businesses", "BusinessCapability")
    BusinessLocation = apps.get_model("businesses", "BusinessLocation")
    for business in Business.objects.all().iterator():
        for code in ("site", "sell", "schedule", "operate"):
            BusinessCapability.objects.get_or_create(business=business, code=code)
        BusinessLocation.objects.get_or_create(
            business=business,
            code="main",
            defaults={
                "name": "Main location",
                "address": business.address,
                "city": business.city,
                "region": business.region,
                "postal_code": business.postal_code,
                "country": business.country,
                "timezone": business.timezone,
                "is_primary": True,
            },
        )
        business.enabled_modules = ["site", "sell", "schedule", "operate"]
        business.save(update_fields=["enabled_modules"])


class Migration(migrations.Migration):
    dependencies = [("businesses", "0003_business_currency_locked_at_and_more")]
    operations = [migrations.RunPython(bootstrap_capabilities, migrations.RunPython.noop)]

