import uuid

from django.db import migrations, models
import django.db.models.deletion

import scheduling.models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0009_event_access_and_capacity"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueevent",
            name="body_font",
            field=models.CharField(default="Manrope", max_length=48),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="closing_message",
            field=models.CharField(blank=True, default="With love", max_length=180),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="heading_font",
            field=models.CharField(default="Bodoni Moda", max_length=48),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="hero_date_text",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="invitation_text",
            field=models.CharField(
                blank=True,
                default="You are invited to celebrate with us.",
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="sections_config",
            field=models.JSONField(
                blank=True,
                default=scheduling.models.default_event_sections,
            ),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="theme_accent",
            field=models.CharField(default="#D6D1C8", max_length=7),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="theme_background",
            field=models.CharField(default="#000000", max_length=7),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="theme_text",
            field=models.CharField(default="#F5F3EE", max_length=7),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="website_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="website_published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="venueevent",
            name="website_template",
            field=models.CharField(
                choices=[("wedding_editorial", "Wedding editorial")],
                default="wedding_editorial",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="eventguest",
            name="wish_approved",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="EventParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("role", models.CharField(blank=True, max_length=80)),
                ("subtitle", models.CharField(blank=True, max_length=160)),
                ("family_text", models.CharField(blank=True, max_length=500)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="scheduling.venueevent")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="EventSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("end_time_label", models.CharField(blank=True, max_length=64)),
                ("venue_name", models.CharField(max_length=180)),
                ("address", models.CharField(blank=True, max_length=500)),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("map_url", models.URLField(blank=True, max_length=500)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schedule_entries", to="scheduling.venueevent")),
            ],
            options={"ordering": ["sort_order", "starts_at", "id"]},
        ),
        migrations.CreateModel(
            name="EventStoryBlock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(blank=True, max_length=160)),
                ("body", models.TextField(max_length=4000)),
                ("date_label", models.CharField(blank=True, max_length=80)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="story_blocks", to="scheduling.venueevent")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="EventQuote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_enabled", models.BooleanField(default=False)),
                ("original_text", models.TextField(blank=True, max_length=2000)),
                ("translation", models.TextField(blank=True, max_length=2000)),
                ("citation", models.CharField(blank=True, max_length=240)),
                ("event", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="quote", to="scheduling.venueevent")),
            ],
        ),
        migrations.CreateModel(
            name="EventMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("image", models.ImageField(max_length=500, upload_to=scheduling.models.venue_event_media_path)),
                ("placement", models.CharField(choices=[("hero", "Hero"), ("story", "Story"), ("gallery", "Gallery"), ("closing", "Closing")], default="gallery", max_length=16)),
                ("caption", models.CharField(blank=True, max_length=240)),
                ("alt_text", models.CharField(max_length=240)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_featured", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media", to="scheduling.venueevent")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
    ]
