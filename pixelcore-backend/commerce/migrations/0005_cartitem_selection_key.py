from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("commerce", "0004_discounts_portal")]
    operations = [
        migrations.RemoveConstraint(model_name="cartitem", name="unique_cart_offering_variant"),
        migrations.AddField(model_name="cartitem", name="selection_key", field=models.CharField(default="", max_length=64)),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(fields=("cart", "offering", "variant", "selection_key"), name="unique_cart_offering_selection", nulls_distinct=False),
        ),
    ]
