from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from smokey_assistant.models import ProviderConnection, GenerationRequest
from .models import Business, BusinessCapability, BusinessMembership


class SmokeyAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="assistant-api")
        self.business = Business.objects.create(
            display_name="API shop", created_by=self.user
        )
        self.member = BusinessMembership.objects.create(
            business=self.business, user=self.user, role="owner"
        )
        self.capability = BusinessCapability.objects.create(
            business=self.business, code="smokey", status="active"
        )
        self.root = f"/api/businesses/{self.business.public_id}/smokey/"
        self.client.force_authenticate(self.user)

    def connection(self):
        response = self.client.post(
            self.root + "connections/",
            {
                "name": "Reports",
                "provider": "openai",
                "model": "fixture-model",
                "permitted_models": ["fixture-model"],
                "secret": "private-fixture-key",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_settings_connections_never_return_keys_and_manager_cannot_edit(self):
        connection = self.connection()
        self.assertNotIn(
            "private-fixture-key", str(self.client.get(self.root + "connections/").data)
        )
        self.member.role = "manager"
        self.member.save()
        self.assertEqual(self.client.get(self.root + "settings/").status_code, 200)
        self.assertEqual(
            self.client.patch(
                self.root + "settings/", {"presentation": "modal"}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(
                self.root + f"connections/{connection['id']}/"
            ).status_code,
            403,
        )

    def test_enable_optional_module_and_validate_models(self):
        self.capability.delete()
        response = self.client.patch(
            f"/api/businesses/{self.business.public_id}/capabilities/smokey/",
            {"status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(
            "smokey", Business.objects.get(pk=self.business.pk).enabled_modules
        )
        self.assertEqual(
            self.client.post(
                self.root + "connections/",
                {"name": "No", "provider": "other", "secret": "secret"},
                format="json",
            ).status_code,
            400,
        )

    def test_cross_tenant_and_disabled_api_are_denied(self):
        connection = self.connection()
        other = Business.objects.create(display_name="Other", created_by=self.user)
        BusinessMembership.objects.create(business=other, user=self.user, role="owner")
        BusinessCapability.objects.create(
            business=other, code="smokey", status="active"
        )
        foreign = (
            f"/api/businesses/{other.public_id}/smokey/connections/{connection['id']}/"
        )
        self.assertEqual(self.client.delete(foreign).status_code, 404)
        self.capability.status = "disabled"
        self.capability.save()
        self.assertEqual(self.client.get(self.root + "settings/").status_code, 403)

    @patch("businesses.smokey_views.generate_smokey_report.delay")
    def test_generation_is_idempotent_and_read_does_not_generate(self, dispatch):
        connection = self.connection()
        item = ProviderConnection.objects.get(public_id=connection["id"])
        item.status = "ready"
        item.save()
        self.client.patch(
            self.root + "settings/",
            {"default_connection_id": connection["id"]},
            format="json",
        )
        body = {
            "prompt": "Report today",
            "plan": {
                "kind": "attendance",
                "date_from": "2026-10-26",
                "date_to": "2026-10-26",
            },
        }
        first = self.client.post(
            self.root + "generations/",
            body,
            format="json",
            HTTP_IDEMPOTENCY_KEY="same-request",
        )
        second = self.client.post(
            self.root + "generations/",
            body,
            format="json",
            HTTP_IDEMPOTENCY_KEY="same-request",
        )
        self.assertEqual(first.status_code, 202, first.data)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(GenerationRequest.objects.count(), 1)
        self.assertEqual(
            self.client.get(self.root + f"generations/{first.data['id']}/").status_code,
            200,
        )

    def test_public_and_staff_access_are_denied(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.root + "settings/").status_code, 401)
        self.client.force_authenticate(self.user)
        self.member.role = "staff"
        self.member.save()
        self.assertEqual(self.client.get(self.root + "settings/").status_code, 404)

    def test_saved_rows_search_paginates_full_snapshot_and_keeps_tenant_boundary(self):
        from smokey_assistant.models import ReportSnapshot, ReportDetailRow

        ai = self.connection()
        request = GenerationRequest.objects.create(
            tenant_id=f"pixelcore:{self.business.public_id}", actor_id=str(self.user.pk),
            idempotency_key="saved-rows", prompt="Sales", connection_revision=1,
            provider="openai", model="fixture-model",
        )
        report = ReportSnapshot.objects.create(
            tenant_id=request.tenant_id, request=request, title="Sales", facts={"tables": {}}, narrative={},
        )
        ReportDetailRow.objects.bulk_create([
            ReportDetailRow(report=report, table_key="transactions", ordinal=index,
                data={"product": "Canvas tote" if index == 104 else "Tee", "sku": str(index), "image_url": "/media/product.jpg"})
            for index in range(105)
        ])
        path = self.root + f"reports/{report.public_id}/tables/transactions/"
        result = self.client.get(path, {"search": "canvas", "page_size": 20})
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["count"], 1)
        self.assertEqual(result.data["results"][0]["sku"], "104")
        self.assertEqual(result.data["results"][0]["image_url"], "http://testserver/media/product.jpg")
        result = self.client.get(path, {"offset": 100, "page_size": 20})
        self.assertEqual(len(result.data["results"]), 5)
        self.assertEqual(result.data["count"], 105)
        self.assertEqual(self.client.get(path, {"page_size": 999}).status_code, 400)
        other = Business.objects.create(display_name="Other", created_by=self.user)
        BusinessMembership.objects.create(business=other, user=self.user, role="owner")
        BusinessCapability.objects.create(business=other, code="smokey", status="active")
        self.assertEqual(self.client.get(path.replace(str(self.business.public_id), str(other.public_id))).status_code, 404)

    @patch("smokey_assistant.providers.openai.OpenAIProvider.catalog")
    def test_failed_catalog_probe_revokes_previous_readiness(self, catalog):
        from smokey_assistant.contracts import AssistantError

        item = self.connection()
        ProviderConnection.objects.filter(public_id=item["id"]).update(status="ready")
        catalog.side_effect = AssistantError("Rejected key", "INVALID_CREDENTIAL", 502)
        response = self.client.post(self.root + f"connections/{item['id']}/check/")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            ProviderConnection.objects.get(public_id=item["id"]).status, "invalid"
        )

    @patch("businesses.smokey_views.generate_smokey_report.delay")
    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    @patch("smokey_assistant.providers.openai.OpenAIProvider.catalog")
    def test_first_verified_connection_enables_generation(
        self, catalog, summarize, dispatch
    ):
        from smokey_assistant.contracts import ProviderResult

        item = self.connection()
        self.assertIsNone(
            self.client.get(self.root + "settings/").data["default_connection_id"]
        )
        catalog.return_value = [{"id": "fixture-model"}]
        summarize.return_value = ProviderResult(
            {"summary": "Verified", "highlights": []}, 10, 5
        )
        response = self.client.post(self.root + f"connections/{item['id']}/check/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "ready")
        self.assertEqual(
            self.client.get(self.root + "settings/").data["default_connection_id"],
            item["id"],
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.root + "generations/",
                {"prompt": "Sales today"},
                format="json",
                HTTP_IDEMPOTENCY_KEY="first-verified-request",
            )
        self.assertEqual(response.status_code, 202, response.data)
        self.assertEqual(response.data["state"], "queued")
        dispatch.assert_called_once()

    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    @patch("smokey_assistant.providers.openai.OpenAIProvider.catalog")
    def test_verifying_another_connection_preserves_explicit_default(
        self, catalog, summarize
    ):
        from smokey_assistant.contracts import ProviderResult

        first, second = self.connection(), self.connection()
        ProviderConnection.objects.filter(public_id=first["id"]).update(status="ready")
        self.client.patch(
            self.root + "settings/",
            {"default_connection_id": first["id"]},
            format="json",
        )
        catalog.return_value = [{"id": "fixture-model"}]
        summarize.return_value = ProviderResult(
            {"summary": "Verified", "highlights": []}, 10, 5
        )
        response = self.client.post(self.root + f"connections/{second['id']}/check/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.client.get(self.root + "settings/").data["default_connection_id"],
            first["id"],
        )

    @patch("smokey_assistant.providers.openai.OpenAIProvider.catalog")
    def test_failed_verification_does_not_select_default(self, catalog):
        from smokey_assistant.contracts import AssistantError

        item = self.connection()
        catalog.side_effect = AssistantError("Rejected key", "INVALID_CREDENTIAL", 502)
        response = self.client.post(self.root + f"connections/{item['id']}/check/")
        self.assertEqual(response.status_code, 502)
        self.assertIsNone(
            self.client.get(self.root + "settings/").data["default_connection_id"]
        )

    @patch("smokey_assistant.providers.openai.OpenAIProvider.summarize")
    @patch("smokey_assistant.providers.openai.OpenAIProvider.catalog")
    def test_changed_connection_cannot_become_default_from_stale_check(
        self, catalog, summarize
    ):
        from django.db.models import F
        from smokey_assistant.contracts import ProviderResult

        item = self.connection()
        catalog.return_value = [{"id": "fixture-model"}]

        def changed_during_call(*args):
            ProviderConnection.objects.filter(public_id=item["id"]).update(
                revision=F("revision") + 1, status="untested"
            )
            return ProviderResult({"summary": "Verified", "highlights": []}, 10, 5)

        summarize.side_effect = changed_during_call
        response = self.client.post(self.root + f"connections/{item['id']}/check/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "untested")
        self.assertIsNone(
            self.client.get(self.root + "settings/").data["default_connection_id"]
        )

    def test_default_repair_only_selects_one_valid_ready_connection_per_tenant(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        from smokey_assistant.models import AssistantSettings

        migration = import_module("smokey_assistant.migrations.0004_verified_default")
        configs = {}
        for tenant, statuses in {
            "single": ["ready"],
            "multiple": ["ready", "ready"],
            "untested": ["untested"],
            "invalid": ["invalid"],
            "empty": [],
            "unpermitted": ["ready"],
            "explicit": ["ready", "ready"],
        }.items():
            config = AssistantSettings.objects.create(tenant_id=tenant)
            configs[tenant] = config
            for status in statuses:
                item = ProviderConnection.objects.create(
                    tenant_id=tenant,
                    name="Fixture",
                    provider="openai",
                    model="fixture-model",
                    permitted_models=[] if tenant == "unpermitted" else ["fixture-model"],
                    status=status,
                    encrypted_secret="unused",
                    secret_suffix="used",
                )
            if tenant == "explicit":
                config.default_connection = item
                config.save()
                explicit_default = item.pk
        migration.select_unambiguous_defaults(
            apps, SimpleNamespace(connection=connection)
        )
        for tenant, config in configs.items():
            config.refresh_from_db()
            if tenant == "single":
                self.assertEqual(config.default_connection.tenant_id, tenant)
            elif tenant == "explicit":
                self.assertEqual(config.default_connection_id, explicit_default)
            else:
                self.assertIsNone(config.default_connection_id, tenant)

    def test_custom_mascot_requires_valid_private_image_and_grid(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile

        result = self.client.patch(
            self.root + "settings/", {"mascot": {"mode": "custom"}}, format="json"
        )
        self.assertEqual(result.status_code, 400)
        buffer = BytesIO()
        Image.new("RGBA", (10, 10), "white").save(buffer, "PNG")
        upload = SimpleUploadedFile(
            "cat.png", buffer.getvalue(), content_type="image/png"
        )
        self.assertEqual(
            self.client.post(
                self.root + "asset/", {"file": upload}, format="multipart"
            ).status_code,
            200,
        )
        result = self.client.patch(
            self.root + "settings/",
            {
                "mascot": {
                    "mode": "custom",
                    "asset_type": "sprite",
                    "columns": 3,
                    "rows": 1,
                }
            },
            format="json",
        )
        self.assertEqual(result.status_code, 400)
        result = self.client.patch(
            self.root + "settings/",
            {
                "mascot": {
                    "mode": "custom",
                    "asset_type": "sprite",
                    "columns": 2,
                    "rows": 1,
                }
            },
            format="json",
        )
        self.assertEqual(result.status_code, 200)
        asset = self.client.get(self.root + "asset/")
        self.assertEqual(asset["Cache-Control"], "private, no-store")

    @patch("smokey_assistant.providers.openai.OpenAIProvider.catalog")
    def test_models_can_be_selected_before_saving_a_connection(self, catalog):
        catalog.return_value = [
            {"id": "fixture-model", "provider": "openai", "name": "Fixture"}
        ]
        response = self.client.post(
            self.root + "models/",
            {"provider": "openai", "secret": "private-discovery-key"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["models"][0]["id"], "fixture-model")
        self.assertEqual(ProviderConnection.objects.count(), 0)
        self.assertNotIn("private-discovery-key", str(response.data))
        item = self.connection()
        response = self.client.get(self.root + f"connections/{item['id']}/models/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["models"][0]["id"], "fixture-model")

    def test_manual_credits_keep_verified_connection_and_revision(self):
        connection = self.connection()
        item = ProviderConnection.objects.get(public_id=connection["id"])
        item.status = "ready"
        item.save(update_fields=["status"])
        revision = item.revision
        response = self.client.patch(
            self.root + f"connections/{item.public_id}/",
            {"credits_usd": "25.50"}, format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["credits_usd"], "25.50")
        self.assertEqual(response.data["status"], "ready")
        item.refresh_from_db()
        self.assertEqual(item.revision, revision)
        self.assertEqual(response.data["usage_by_model"], [])
        self.assertNotIn("encrypted_secret", response.data)
        self.assertEqual(
            self.client.patch(self.root + f"connections/{item.public_id}/",
                              {"credits_usd": None}, format="json").data["credits_usd"],
            None,
        )

    def test_manual_credits_validate_amount_and_owner_permission(self):
        connection = self.connection()
        path = self.root + f"connections/{connection['id']}/"
        for value in ["-1", "0", "1.001", "10000000000.00", "NaN"]:
            self.assertEqual(self.client.patch(path, {"credits_usd": value}, format="json").status_code, 400)
        self.member.role = "manager"
        self.member.save()
        self.assertEqual(self.client.patch(path, {"credits_usd": "10.00"}, format="json").status_code, 403)

    def test_connection_lifetime_usage_is_scoped_and_includes_old_models(self):
        from datetime import timedelta
        from django.utils import timezone
        from smokey_assistant.models import UsageAttempt
        from smokey_assistant.connections import connection_usage
        connection = self.connection()
        item = ProviderConnection.objects.get(public_id=connection["id"])
        attempt = UsageAttempt.objects.create(
            tenant_id=item.tenant_id, connection_id_snapshot=str(item.public_id),
            provider="openai", model="gpt-4.1-mini", purpose="summary",
            outcome="succeeded", input_tokens=2000, output_tokens=500,
            reserved_tokens=4000, periods=[],
        )
        UsageAttempt.objects.filter(pk=attempt.pk).update(created_at=timezone.now() - timedelta(days=90))
        UsageAttempt.objects.create(
            tenant_id=item.tenant_id, connection_id_snapshot=str(item.public_id),
            provider="openai", model="gpt-4.1", purpose="classify",
            outcome="failed", input_tokens=100, output_tokens=None,
            reserved_tokens=1000, periods=[],
        )
        UsageAttempt.objects.create(
            tenant_id="pixelcore:other-business", connection_id_snapshot=str(item.public_id),
            provider="openai", model="gpt-4.1-mini", purpose="summary",
            outcome="succeeded", input_tokens=999999, output_tokens=999999,
            reserved_tokens=2000000, periods=[],
        )
        with self.assertNumQueries(1):
            groups = connection_usage(item.tenant_id, [str(item.public_id)])
        rows = {row["model"]: row for row in groups[str(item.public_id)]}
        self.assertEqual(rows["gpt-4.1-mini"]["input_tokens"], 2000)
        self.assertEqual(rows["gpt-4.1"]["unknown"], 1)
        response = self.client.get(self.root + "connections/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data[0]["usage_by_model"]), 2)
