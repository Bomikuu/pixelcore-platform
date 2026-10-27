"""Isolated assistant checks; never supplies production credentials."""

from .settings import *  # noqa: F403

SMOKEY_ENCRYPTION_KEYS = ["MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="]
CELERY_TASK_ALWAYS_EAGER = True
SECURE_SSL_REDIRECT = False
if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    DATABASES["default"]["TEST"] = {"NAME": "test_smokey_assistant"}
if "smokey_assistant" not in INSTALLED_APPS:
    INSTALLED_APPS.append("smokey_assistant")
