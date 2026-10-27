from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection, close_old_connections
from django.test import TransactionTestCase
from smokey_assistant.contracts import AssistantError
from smokey_assistant.credentials import encrypt_secret
from smokey_assistant.generation import start_generation, run_generation
from smokey_assistant.models import (
    AssistantSettings,
    ProviderConnection,
    ReportSnapshot,
    UsageBucket,
)
from smokey_assistant.quotas import reserve
from .models import Business, BusinessMembership, BusinessCapability
from .smokey_bridge import context_for, worker_context
from .smokey_reports import resolve_report


@skipUnless(
    connection.vendor == "postgresql", "Transactional concurrency requires PostgreSQL"
)
class SmokeyConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="race-owner")
        self.business = Business.objects.create(
            display_name="Concurrency", created_by=self.user
        )
        BusinessMembership.objects.create(
            business=self.business, user=self.user, role="owner"
        )
        BusinessCapability.objects.create(
            business=self.business, code="smokey", status="active"
        )
        self.context = context_for(self.user, self.business.public_id, "generate")
        self.ai = ProviderConnection.objects.create(
            tenant_id=self.context.tenant_id,
            name="Mock",
            provider="openai",
            model="test-model",
            permitted_models=["test-model"],
            encrypted_secret=encrypt_secret("test-key"),
            secret_suffix="-key",
            status="ready",
        )
        self.config = AssistantSettings.objects.create(
            tenant_id=self.context.tenant_id,
            default_connection=self.ai,
            daily_requests=1,
        )

    def thread(self, action):
        close_old_connections()
        try:
            return action()
        finally:
            connection.close()

    def test_concurrent_reservations_cannot_exceed_budget(self):
        def attempt():
            try:
                reserve(self.context, self.ai, "summary", {}, 512)
                return "reserved"
            except AssistantError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.thread(attempt), range(2)))
        self.assertCountEqual(results, ["reserved", "APP_QUOTA"])
        self.assertEqual(
            UsageBucket.objects.filter(
                tenant_id=self.context.tenant_id, period__regex=r"^\d{4}-\d{2}-\d{2}$"
            )
            .get()
            .requests,
            1,
        )

    def test_duplicate_workers_create_only_one_snapshot(self):
        item, _ = start_generation(
            self.context,
            "Attendance",
            {"kind": "attendance", "date_from": "2026-10-26", "date_to": "2026-10-26"},
            "race-request",
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(
                pool.map(
                    lambda _: self.thread(
                        lambda: run_generation(
                            item.public_id, worker_context, resolve_report
                        )
                    ),
                    range(2),
                )
            )
        self.assertEqual(ReportSnapshot.objects.count(), 1)
