import businesses.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("businesses", "0004_bootstrap_business_capabilities"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="industry_preset",
            field=models.CharField(
                choices=[("general", "General business"), ("restaurant", "Restaurant"), ("retail", "Retail"), ("services", "Services"), ("hybrid", "Hybrid")],
                default="general",
                max_length=24,
            ),
        ),
        migrations.CreateModel(
            name="AccountProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("email_verified_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="account_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="accountprofile",
            constraint=models.UniqueConstraint(condition=models.Q(("phone", ""), _negated=True), fields=("phone",), name="unique_nonblank_account_phone"),
        ),
        migrations.CreateModel(
            name="AccountChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("purpose", models.CharField(choices=[("verify_email", "Verify email"), ("reset_password", "Reset password")], max_length=24)),
                ("code_digest", models.CharField(max_length=64)),
                ("expires_at", models.DateTimeField(default=businesses.models.account_challenge_expiry)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="account_challenges", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(
            model_name="accountchallenge",
            index=models.Index(fields=["user", "purpose", "expires_at"], name="businesses__user_id_568e78_idx"),
        ),
    ]
