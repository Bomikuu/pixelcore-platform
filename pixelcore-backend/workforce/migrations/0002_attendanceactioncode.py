import django.db.models.deletion
import uuid

from django.db import migrations, models

import workforce.models


class Migration(migrations.Migration):
    dependencies = [
        ("workforce", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceActionCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("clock_in", "Clock in"),
                            ("clock_out", "Clock out"),
                        ],
                        max_length=12,
                    ),
                ),
                ("code_digest", models.CharField(db_index=True, max_length=64)),
                (
                    "expires_at",
                    models.DateTimeField(
                        default=workforce.models.attendance_action_code_expiry
                    ),
                ),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_action_codes",
                        to="businesses.business",
                    ),
                ),
                (
                    "staff",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_action_codes",
                        to="scheduling.staffprofile",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="attendanceactioncode",
            index=models.Index(
                fields=["business", "code_digest", "expires_at"],
                name="workforce_action_code_lookup",
            ),
        ),
    ]
