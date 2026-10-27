import json
from datetime import date

from django.test import TestCase, override_settings
from smokey_assistant.contracts import ReportPlan, AssistantError
from smokey_assistant.credentials import encrypt_secret, decrypt_secret
from smokey_assistant.connections import connection_payload
from smokey_assistant.models import ProviderConnection


class SmokeyContractTests(TestCase):
    def test_credentials_are_encrypted_and_never_serialized(self):
        secret = "test-private-credential"
        encrypted = encrypt_secret(secret)
        self.assertNotEqual(encrypted, secret)
        self.assertEqual(decrypt_secret(encrypted), secret)
        connection = ProviderConnection.objects.create(
            tenant_id="test:one",
            name="Office",
            provider="openai",
            model="test-model",
            encrypted_secret=encrypted,
            secret_suffix=secret[-4:],
        )
        self.assertNotIn(secret, json.dumps(connection_payload(connection)))

    def test_invalid_report_plan_is_rejected(self):
        for kind, start, end in [
            ("sql", "2026-01-01", "2026-01-02"),
            ("daily", "2026-02-02", "2026-02-01"),
        ]:
            with self.assertRaises(AssistantError):
                ReportPlan.parse({"kind": kind, "date_from": start, "date_to": end})
        self.assertEqual(
            ReportPlan.parse(
                {"kind": "daily", "date_from": "2026-01-01", "date_to": "2026-01-01"}
            ).date_from,
            date(2026, 1, 1),
        )

    @override_settings(SMOKEY_ENCRYPTION_KEYS=[])
    def test_missing_encryption_configuration_fails_closed(self):
        with self.assertRaises(AssistantError):
            encrypt_secret("private")
