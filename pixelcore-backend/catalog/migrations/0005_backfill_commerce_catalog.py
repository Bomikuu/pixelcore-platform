from django.db import migrations


def forwards(apps, schema_editor):
    Offering = apps.get_model("catalog", "Offering")
    OfferingMedia = apps.get_model("catalog", "OfferingMedia")
    ProductProfile = apps.get_model("catalog", "ProductProfile")
    VariantDimension = apps.get_model("catalog", "VariantDimension")
    VariantValue = apps.get_model("catalog", "VariantValue")

    for offering in Offering.objects.all().iterator():
        if offering.offering_type != "service":
            ProductProfile.objects.get_or_create(business_id=offering.business_id, offering_id=offering.id)

        image_assets = list(offering.assets.filter(asset_type="image").order_by("id"))
        for index, asset in enumerate(image_assets):
            OfferingMedia.objects.get_or_create(
                business_id=offering.business_id,
                offering_id=offering.id,
                asset_id=asset.id,
                variant_id=None,
                role="cover" if index == 0 else "gallery",
                defaults={"sort_order": index},
            )

        variants = list(offering.variants.order_by("sort_order", "id"))
        if not variants or offering.variant_dimensions.exists():
            continue
        dimension = VariantDimension.objects.create(
            business_id=offering.business_id,
            offering_id=offering.id,
            name="Option",
            display_type="text",
            sort_order=0,
        )
        used_labels = set()
        for index, variant in enumerate(variants):
            base = (variant.name or variant.sku or f"Option {index + 1}")[:90]
            label = base
            suffix = 2
            while label.lower() in used_labels:
                label = f"{base[:85]} {suffix}"
                suffix += 1
            used_labels.add(label.lower())
            value = VariantValue.objects.create(
                business_id=offering.business_id,
                dimension_id=dimension.id,
                label=label,
                sort_order=index,
            )
            variant.combination_key = str(value.public_id)
            attributes = dict(variant.attributes or {})
            attributes.setdefault("Option", label)
            variant.attributes = attributes
            variant.save(update_fields=["combination_key", "attributes"])
            variant.option_values.add(value)


def backwards(apps, schema_editor):
    Offering = apps.get_model("catalog", "Offering")
    for offering in Offering.objects.all().iterator():
        offering.variants.update(combination_key="")
    apps.get_model("catalog", "VariantDimension").objects.all().delete()
    apps.get_model("catalog", "OfferingMedia").objects.all().delete()
    apps.get_model("catalog", "ProductProfile").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_offeringvariant_barcode_and_more")]
    operations = [migrations.RunPython(forwards, backwards)]
