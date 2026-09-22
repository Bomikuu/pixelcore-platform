from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0008_venueevent_thumbnail"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="max_guests",
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="organizer_token_ciphertext",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="eventguest",
            name="invite_token_ciphertext",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="eventguest",
            name="invite_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
