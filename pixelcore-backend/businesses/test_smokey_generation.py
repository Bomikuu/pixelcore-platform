from unittest.mock import patch
from smokey_assistant.contracts import AssistantError, ProviderResult
from smokey_assistant.credentials import encrypt_secret
from smokey_assistant.generation import (
    start_generation,
    run_generation,
    cancel_generation,
)
from smokey_assistant.models import AssistantSettings, ProviderConnection, UsageAttempt
from .test_smokey_reports import SmokeyReportTests
from .smokey_bridge import context_for, worker_context
from .models import BusinessMembership, BusinessCapability
from .smokey_reports import resolve_report


class SmokeyGenerationTests(SmokeyReportTests):
    def setUp(self):
        super().setUp()
        BusinessMembership.objects.create(
            business=self.business, user=self.user, role="owner"
        )
        BusinessCapability.objects.create(
            business=self.business, code="smokey", status="active"
        )
        self.context = context_for(self.user, self.business.public_id, "generate")
        self.connection = ProviderConnection.objects.create(
            tenant_id=self.context.tenant_id,
            name="AI",
            provider="openai",
            model="test-model",
            permitted_models=["test-model"],
            status="ready",
            encrypted_secret=encrypt_secret("test-private-key"),
            secret_suffix="-key",
        )
        self.config = AssistantSettings.objects.create(
            tenant_id=self.context.tenant_id, default_connection=self.connection
        )
        self.plan = {
            "kind": "daily",
            "date_from": "2026-10-26",
            "date_to": "2026-10-26",
        }

    def start(self, key="fixture-key"):
        return start_generation(self.context, "Report today", self.plan, key)[0]

    def test_idempotency_empty_report_and_replayed_worker(self):
        request = self.start()
        self.assertEqual(self.start().pk, request.pk)
        run_generation(request.public_id, worker_context, resolve_report)
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "empty")
        self.assertEqual(request.report.facts["metrics"]["orders"], 0)
        self.assertEqual(request.attempts.count(), 0)

    def test_disabled_capability_prevents_work(self):
        request = self.start()
        BusinessCapability.objects.filter(business=self.business, code="smokey").update(
            status="disabled"
        )
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "failed")
        self.assertFalse(hasattr(request, "report"))

    def test_cancelled_request_does_not_run(self):
        request = self.start()
        cancel_generation(self.context, request.public_id)
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "cancelled")

    def test_unknown_usage_retains_reservation_and_blocks_next_call(self):
        from smokey_assistant.quotas import reserve, settle

        self.config.daily_tokens = 10000
        self.config.save()
        attempt = reserve(self.context, self.connection, "summary", {}, 100)
        settle(
            attempt, error=AssistantError("Timeout", "PROVIDER_UNAVAILABLE", 502, True)
        )
        attempt.refresh_from_db()
        self.assertEqual(attempt.outcome, "unknown")
        with self.assertRaises(AssistantError):
            reserve(self.context, self.connection, "summary", {}, 100)

    def populated_report(self):
        from datetime import datetime, timezone
        from commerce.models import Order

        item = Order.objects.create(
            business=self.business,
            number="SUMMARY-1",
            currency="PHP",
            subtotal="99.00",
            grand_total="99.00",
        )
        Order.objects.filter(pk=item.pk).update(
            placed_at=datetime(2026, 10, 26, 1, tzinfo=timezone.utc)
        )
        return item

    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    def test_success_records_usage_and_snapshot_is_immutable(self, summarize):
        order = self.populated_report()
        summarize.return_value = ProviderResult(
            {"summary": "One order was recorded.", "highlights": []}, 100, 20
        )
        request = self.start()
        run_generation(request.public_id, worker_context, resolve_report)
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "succeeded")
        self.assertEqual(summarize.call_count, 1)
        self.assertEqual(request.attempts.get().input_tokens, 100)
        order.grand_total = "999.00"
        order.save()
        self.assertEqual(request.report.facts["metrics"]["ordered_sales"], "99.00")
        self.assertEqual(
            request.report.rows.get(table_key="orders").data["total"], "99.00"
        )

    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    def test_cancellation_during_provider_call_keeps_usage_without_publishing(
        self, summarize
    ):
        self.populated_report()
        request = self.start()

        def cancel_then_return(*args):
            cancel_generation(self.context, request.public_id)
            return ProviderResult({"summary": "One order.", "highlights": []}, 100, 20)

        summarize.side_effect = cancel_then_return
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "cancelled")
        self.assertFalse(hasattr(request, "report"))
        self.assertEqual(request.attempts.get().output_tokens, 20)

    def test_connection_revision_change_prevents_dispatch(self):
        request = self.start()
        self.connection.revision += 1
        self.connection.save()
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.error_code, "CONNECTION_CHANGED")
        self.assertEqual(request.attempts.count(), 0)

    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    def test_collections_without_new_orders_are_not_an_empty_report(self, summarize):
        from smokey_assistant.contracts import ResolvedReport

        summarize.return_value = ProviderResult(
            {
                "summary": "Payments were collected against existing invoices.",
                "highlights": [],
            },
            100,
            20,
        )
        request = self.start()

        def facts(context, plan):
            return ResolvedReport(
                {
                    "kind": "daily",
                    "metrics": {"orders": 0, "collected_payments": "90.00"},
                    "tables": {"orders": {"total": 0}},
                    "unavailable_sources": [],
                },
                [],
            )

        run_generation(request.public_id, worker_context, facts)
        request.refresh_from_db()
        self.assertEqual(request.state, "succeeded")
        self.assertEqual(summarize.call_count, 1)

    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    def test_cancel_during_reservation_prevents_a_new_paid_call(self, summarize):
        from smokey_assistant.quotas import reserve as actual_reserve

        self.populated_report()
        request = self.start()

        def reserve_then_stop(*args):
            attempt = actual_reserve(*args)
            cancel_generation(self.context, request.public_id)
            return attempt

        with patch(
            "smokey_assistant.generation.reserve", side_effect=reserve_then_stop
        ):
            run_generation(request.public_id, worker_context, resolve_report)
        self.assertEqual(summarize.call_count, 0)
        self.assertEqual(request.attempts.get().outcome, "not_sent")
        from smokey_assistant.models import UsageBucket

        self.assertTrue(
            all(
                bucket.tokens == 0 and bucket.requests == 0
                for bucket in UsageBucket.objects.all()
            )
        )

    def test_usage_distinguishes_cancelled_generation_from_successful_provider_call(
        self,
    ):
        from datetime import timedelta
        from django.utils import timezone
        from smokey_assistant.usage import usage_summary

        request = self.start()
        cancel_generation(self.context, request.public_id)
        UsageAttempt.objects.create(
            tenant_id=self.context.tenant_id,
            request=request,
            connection_id_snapshot=str(self.connection.public_id),
            provider="openai",
            model="test-model",
            purpose="summary",
            outcome="succeeded",
            input_tokens=100,
            output_tokens=20,
            reserved_tokens=1000,
        )
        result = usage_summary(
            self.context,
            timezone.now() - timedelta(days=1),
            timezone.now() + timedelta(days=1),
        )
        self.assertEqual(result["attempts"][0]["generation_state"], "cancelled")
        self.assertEqual(result["attempts"][0]["actor_id"], str(self.user.pk))

    @patch("smokey_assistant.providers.openai.OpenAIProvider.classify")
    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    def test_free_text_request_classifies_then_summarizes_once(
        self, summarize, classify
    ):
        self.populated_report()
        classify.return_value = ProviderResult(
            {**self.plan, "clarification": ""}, 20, 10
        )
        summarize.return_value = ProviderResult(
            {"summary": "One recorded order.", "highlights": []}, 100, 20
        )
        request, _ = start_generation(
            self.context, "Summarize today", None, "free-text-key"
        )
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "succeeded")
        self.assertEqual(classify.call_count, 1)
        self.assertEqual(summarize.call_count, 1)
        self.assertEqual(request.attempts.count(), 2)
        replay, created = start_generation(
            self.context, "Summarize today", None, "free-text-key"
        )
        self.assertFalse(created)
        self.assertEqual(replay.pk, request.pk)

    @patch("smokey_assistant.providers.openai.OpenAIProvider.classify")
    def test_unsupported_free_text_asks_for_clarification_without_a_report(
        self, classify
    ):
        classify.return_value = ProviderResult(
            {
                "kind": "clarify",
                "date_from": "",
                "date_to": "",
                "clarification": "Choose sales, attendance or late arrivals.",
            },
            20,
            10,
        )
        request, _ = start_generation(
            self.context, "Run arbitrary SQL", None, "clarify-key"
        )
        run_generation(request.public_id, worker_context, resolve_report)
        request.refresh_from_db()
        self.assertEqual(request.state, "empty")
        self.assertIn("Choose", request.clarification)
        self.assertFalse(hasattr(request, "report"))
