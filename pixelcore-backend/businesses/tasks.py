from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from urllib.parse import urlencode


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_account_code(email, first_name, purpose, code):
    if purpose == "verify_email":
        subject = "Verify your PixelCore account"
        action = "verify your email"
    else:
        subject = "Reset your PixelCore password"
        action = "reset your password"
    greeting = f"Hi {first_name}," if first_name else "Hello,"
    send_mail(
        subject,
        f"{greeting}\n\nUse {code} to {action}. This code expires in 15 minutes.\n\nIf you did not request this, you can ignore this message.",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_team_invitation(invitation_id, raw_token):
    from .models import BusinessInvitation

    invitation = BusinessInvitation.objects.select_related("business", "invited_by").get(pk=invitation_id)
    query = urlencode({"token": raw_token})
    invitation_url = f"{settings.PIXELCORE_FRONTEND_URL.rstrip('/')}/employee-onboarding?{query}"
    send_mail(
        f"Join {invitation.business.display_name} on PixelCore",
        (
            f"{invitation.invited_by.get_full_name() or invitation.invited_by.email} "
            f"invited you as {invitation.get_role_display().lower()}.\n\n"
            f"Create or connect your employee account: {invitation_url}\n\n"
            f"This link expires on {invitation.expires_at.isoformat()}."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [invitation.email],
    )

# Celery autodiscovers tasks.py; assistant imports stay inside task execution.
from .smokey_tasks import generate_smokey_report, recover_smokey_reports  # noqa: F401
