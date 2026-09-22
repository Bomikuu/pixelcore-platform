from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scheduling", "0002_resources_and_staff_operations")]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
