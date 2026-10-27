from datetime import datetime, time, timedelta
from importlib.resources import files
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from smokey_assistant.assets_api import validated_asset
from smokey_assistant.connections import connection_payload, connection_usage
from smokey_assistant.contracts import AssistantError, ReportPlan
from smokey_assistant.credentials import encrypt_secret, decrypt_secret
from smokey_assistant.generation import (
    start_generation,
    cancel_generation,
    recover_expired,
)
from smokey_assistant.models import (
    AssistantSettings,
    ProviderConnection,
    GenerationRequest,
    ReportSnapshot,
)
from smokey_assistant.providers import get_provider
from smokey_assistant.quotas import reserve, settle
from smokey_assistant.usage import usage_summary
from .services import record_audit
from .smokey_bridge import assistant_context, tenant_business
from .smokey_serializers import ConnectionSerializer, SettingsSerializer
from .smokey_tasks import generate_smokey_report


def settings_payload(config, context):
    return {
        "default_connection_id": str(config.default_connection.public_id)
        if config.default_connection
        else None,
        "presentation": config.presentation,
        "mascot": config.mascot,
        "has_mascot_asset": config.mascot_asset is not None,
        **{
            key: getattr(config, key)
            for key in (
                "daily_requests",
                "monthly_requests",
                "daily_tokens",
                "monthly_tokens",
            )
        },
        "permissions": sorted(context.permissions),
        "timezone": context.timezone,
    }


def request_payload(item):
    report = getattr(item, "report", None)
    return {
        "id": str(item.public_id),
        "state": item.state,
        "plan": item.plan,
        "prompt": item.prompt,
        "report_id": str(report.public_id) if report else None,
        "clarification": item.clarification,
        "error": {"code": item.error_code, "message": item.error_message}
        if item.error_code
        else None,
    }


def report_row_payload(row, request):
    image = row.get("image_url")
    if isinstance(image, str) and image.startswith("/media/"):
        return {**row, "image_url": request.build_absolute_uri(image)}
    return row


class SmokeyView(APIView):
    permission_classes = [IsAuthenticated]

    def context(self, request, public_id, action="view_reports"):
        return assistant_context(request, public_id, action)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response

    def handle_exception(self, error):
        if isinstance(error, AssistantError):
            return Response(
                {"error": {"code": error.code, "message": str(error), "details": {}}},
                status=error.status,
            )
        return super().handle_exception(error)


class SmokeySettingsView(SmokeyView):
    def get(self, request, public_id):
        context = self.context(request, public_id)
        config, _ = AssistantSettings.objects.get_or_create(tenant_id=context.tenant_id)
        return Response(settings_payload(config, context))

    @transaction.atomic
    def patch(self, request, public_id):
        context = self.context(request, public_id, "configure")
        serializer = SettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config, _ = AssistantSettings.objects.get_or_create(tenant_id=context.tenant_id)
        config = AssistantSettings.objects.select_for_update().get(pk=config.pk)
        data = serializer.validated_data
        if "default_connection_id" in data:
            identifier = data.pop("default_connection_id")
            config.default_connection = (
                get_object_or_404(
                    ProviderConnection,
                    public_id=identifier,
                    tenant_id=context.tenant_id,
                )
                if identifier
                else None
            )
        for key, value in data.items():
            setattr(config, key, value)
        if config.mascot.get("mode") == "custom":
            if not config.mascot_asset:
                raise AssistantError(
                    "Upload a mascot image before selecting Custom mascot."
                )
            if config.mascot.get("asset_type") == "sprite":
                with Image.open(BytesIO(bytes(config.mascot_asset))) as image:
                    if image.width % config.mascot.get(
                        "columns", 1
                    ) or image.height % config.mascot.get("rows", 1):
                        raise AssistantError(
                            "Sprite columns and rows must divide the image into equal whole-pixel cells."
                        )
        config.save()
        record_audit(
            tenant_business(context),
            request.user,
            "smokey.settings.updated",
            "smokey",
            "settings",
        )
        return Response(settings_payload(config, context))


class SmokeyConnectionsView(SmokeyView):
    def get(self, request, public_id):
        context = self.context(request, public_id)
        connections = list(
            ProviderConnection.objects.filter(tenant_id=context.tenant_id).order_by(
                "created_at"
            )
        )
        usage = connection_usage(
            context.tenant_id, [str(item.public_id) for item in connections]
        )
        return Response(
            [
                connection_payload(item, usage.get(str(item.public_id), []))
                for item in connections
            ]
        )

    def post(self, request, public_id):
        context = self.context(request, public_id, "configure")
        serializer = ConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        secret = data.pop("secret", "")
        if not secret or data["model"] not in data["permitted_models"]:
            raise AssistantError(
                "Supply a key and include the selected model in permitted models."
            )
        get_provider(data["provider"]).validate_model_id(data["model"])
        item = ProviderConnection.objects.create(
            tenant_id=context.tenant_id,
            encrypted_secret=encrypt_secret(secret),
            secret_suffix=secret[-4:],
            **data,
        )
        record_audit(
            tenant_business(context),
            request.user,
            "smokey.connection.created",
            "smokey_connection",
            item.public_id,
        )
        return Response(connection_payload(item), status=201)


class SmokeyConnectionView(SmokeyView):
    @transaction.atomic
    def patch(self, request, public_id, connection_id):
        context = self.context(request, public_id, "configure")
        item = get_object_or_404(
            ProviderConnection.objects.select_for_update(),
            public_id=connection_id,
            tenant_id=context.tenant_id,
        )
        serializer = ConnectionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        secret = data.pop("secret", None)
        needs_verification = bool(set(data) - {"credits_usd"}) or bool(secret)
        for key, value in data.items():
            setattr(item, key, value)
        if needs_verification:
            get_provider(item.provider).validate_model_id(item.model)
            if item.model not in item.permitted_models:
                raise AssistantError("Include the selected model in permitted models.")
            if secret:
                item.encrypted_secret, item.secret_suffix = (
                    encrypt_secret(secret),
                    secret[-4:],
                )
            item.status, item.checked_at, item.revision = (
                "untested",
                None,
                item.revision + 1,
            )
        item.save()
        record_audit(
            tenant_business(context),
            request.user,
            "smokey.connection.updated",
            "smokey_connection",
            item.public_id,
        )
        return Response(connection_payload(item))

    def delete(self, request, public_id, connection_id):
        context = self.context(request, public_id, "configure")
        item = get_object_or_404(
            ProviderConnection, public_id=connection_id, tenant_id=context.tenant_id
        )
        item.delete()
        record_audit(
            tenant_business(context),
            request.user,
            "smokey.connection.deleted",
            "smokey_connection",
            connection_id,
        )
        return Response(status=204)


class SmokeyModelsView(SmokeyView):
    def get(self, request, public_id, connection_id):
        context = self.context(request, public_id, "configure")
        item = get_object_or_404(
            ProviderConnection, public_id=connection_id, tenant_id=context.tenant_id
        )
        return Response(
            {
                "models": get_provider(item.provider).catalog(
                    decrypt_secret(item.encrypted_secret)
                ),
                "checked_at": timezone.now(),
            }
        )


class SmokeyModelDiscoveryView(SmokeyView):
    """Discover before saving so first-time setup never needs a guessed model ID."""

    def post(self, request, public_id):
        self.context(request, public_id, "configure")
        provider = get_provider(request.data.get("provider"))
        secret = request.data.get("secret")
        if not isinstance(secret, str) or not secret.strip() or len(secret) > 1000:
            raise AssistantError(
                "Enter your provider API key to load its model catalog."
            )
        return Response(
            {"models": provider.catalog(secret.strip()), "checked_at": timezone.now()}
        )


class SmokeyConnectionCheckView(SmokeyView):
    def post(self, request, public_id, connection_id):
        context = self.context(request, public_id, "configure")
        item = get_object_or_404(
            ProviderConnection, public_id=connection_id, tenant_id=context.tenant_id
        )
        provider, secret = (
            get_provider(item.provider),
            decrypt_secret(item.encrypted_secret),
        )
        facts = {
            "metrics": {"connection_test": True},
            "instruction": "Confirm this synthetic connection test.",
        }
        attempt = None
        try:
            catalog = provider.catalog(secret)
            if item.model not in {row["id"] for row in catalog}:
                raise AssistantError(
                    "This model was not found in this provider's available catalog.",
                    "MODEL_UNAVAILABLE",
                    409,
                )
            attempt = reserve(context, item, "connection_check", facts, 512)
            result = provider.summarize(secret, item.model, facts, 512)
        except AssistantError as error:
            if attempt:
                settle(
                    attempt, result=getattr(error, "provider_result", None), error=error
                )
            if error.code != "APP_QUOTA":
                ProviderConnection.objects.filter(
                    pk=item.pk, revision=item.revision
                ).update(
                    status="invalid"
                    if error.code in {"INVALID_CREDENTIAL", "MODEL_UNAVAILABLE"}
                    else "unavailable",
                    checked_at=None,
                )
            raise
        settle(attempt, result=result)
        self.context(request, public_id, "configure")
        with transaction.atomic():
            config, _ = AssistantSettings.objects.get_or_create(
                tenant_id=context.tenant_id
            )
            config = AssistantSettings.objects.select_for_update().get(pk=config.pk)
            verified = ProviderConnection.objects.filter(
                pk=item.pk, tenant_id=context.tenant_id, revision=item.revision
            ).update(status="ready", checked_at=timezone.now())
            item.refresh_from_db()
            # Saving a key is not verification. Only a successful, current check
            # can fill an empty default; never replace an administrator's choice.
            if verified and config.default_connection_id is None:
                config.default_connection = item
                config.save(update_fields=["default_connection"])
        return Response(connection_payload(item))


class SmokeyGenerationListView(SmokeyView):
    def post(self, request, public_id):
        context = self.context(request, public_id, "generate")
        item, created = start_generation(
            context,
            request.data.get("prompt"),
            request.data.get("plan"),
            request.headers.get("Idempotency-Key"),
        )
        if created:
            try:
                transaction.on_commit(
                    lambda: generate_smokey_report.delay(str(item.public_id))
                )
            except Exception:
                GenerationRequest.objects.filter(pk=item.pk, state="queued").update(
                    state="failed",
                    error_code="DISPATCH_FAILED",
                    error_message="The report worker is unavailable. Please try again later.",
                    finished_at=timezone.now(),
                )
        item.refresh_from_db()
        return Response(request_payload(item), status=202)


class SmokeyGenerationView(SmokeyView):
    def get(self, request, public_id, generation_id):
        context = self.context(request, public_id)
        recover_expired()
        return Response(
            request_payload(
                get_object_or_404(
                    GenerationRequest,
                    public_id=generation_id,
                    tenant_id=context.tenant_id,
                    actor_id=context.actor_id,
                )
            )
        )


class SmokeyCancelView(SmokeyView):
    def post(self, request, public_id, generation_id):
        context = self.context(request, public_id, "generate")
        get_object_or_404(
            GenerationRequest,
            public_id=generation_id,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )
        return Response(request_payload(cancel_generation(context, generation_id)))


class SmokeyReportsView(SmokeyView):
    def get(self, request, public_id):
        context = self.context(request, public_id)
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            raise AssistantError("Use a valid page offset.") from None
        reports = (
            ReportSnapshot.objects.filter(tenant_id=context.tenant_id)
            .select_related("request")
            .order_by("-created_at")
        )
        return Response(
            {
                "count": reports.count(),
                "results": [
                    {
                        "id": str(item.public_id),
                        "title": item.title,
                        "created_at": item.created_at,
                        "actor_id": item.request.actor_id,
                        "model": item.request.model,
                    }
                    for item in reports[offset : offset + 20]
                ],
            }
        )


class SmokeyReportView(SmokeyView):
    def get(self, request, public_id, report_id):
        context = self.context(request, public_id)
        item = get_object_or_404(
            ReportSnapshot.objects.select_related("request"),
            public_id=report_id,
            tenant_id=context.tenant_id,
        )
        return Response(
            {
                "id": str(item.public_id),
                "title": item.title,
                "facts": {
                    **item.facts,
                    "tables": {
                        key: {
                            **table,
                            "rows": [report_row_payload(row, request) for row in table["rows"]],
                        }
                        for key, table in item.facts["tables"].items()
                    },
                },
                "narrative": item.narrative,
                "created_at": item.created_at,
                "actor_id": item.request.actor_id,
                "provider": item.request.provider,
                "model": item.request.model,
            }
        )

    def delete(self, request, public_id, report_id):
        context = self.context(request, public_id, "delete_reports")
        get_object_or_404(
            ReportSnapshot, public_id=report_id, tenant_id=context.tenant_id
        ).delete()
        record_audit(
            tenant_business(context),
            request.user,
            "smokey.report.deleted",
            "smokey_report",
            report_id,
        )
        return Response(status=204)


class SmokeyReportRowsView(SmokeyView):
    def get(self, request, public_id, report_id, table_key):
        context = self.context(request, public_id)
        report = get_object_or_404(
            ReportSnapshot, public_id=report_id, tenant_id=context.tenant_id
        )
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
            page_size = int(request.query_params.get("page_size", 100))
            if page_size not in {20, 50, 100}:
                raise ValueError
        except ValueError:
            raise AssistantError(
                "Use a valid page offset and a page size of 20, 50 or 100."
            ) from None
        rows = report.rows.filter(table_key=table_key).order_by("ordinal")
        search = request.query_params.get("search", "").strip()[:100]
        if search:
            match = Q()
            for field in ("product", "employee", "order", "sku", "status", "payment"):
                match |= Q(**{f"data__{field}__icontains": search})
            rows = rows.filter(match)
        return Response(
            {
                "count": rows.count(),
                "results": [
                    report_row_payload(row, request) for row in
                    rows[offset : offset + page_size].values_list("data", flat=True)
                ],
            }
        )


class SmokeyUsageView(SmokeyView):
    def get(self, request, public_id):
        context = self.context(request, public_id)
        zone = ZoneInfo(context.timezone)
        today = timezone.localdate(timezone=zone)
        plan = ReportPlan.parse(
            {
                "kind": "daily",
                "date_from": request.query_params.get(
                    "date_from", today.replace(day=1).isoformat()
                ),
                "date_to": request.query_params.get("date_to", today.isoformat()),
            }
        )
        return Response(
            usage_summary(
                context,
                datetime.combine(plan.date_from, time.min, zone),
                datetime.combine(plan.date_to + timedelta(days=1), time.min, zone),
            )
        )


class SmokeyAssetView(SmokeyView):
    def get(self, request, public_id):
        context = self.context(request, public_id)
        config, _ = AssistantSettings.objects.get_or_create(tenant_id=context.tenant_id)
        data = (
            bytes(config.mascot_asset)
            if config.mascot_asset
            else files("smokey_assistant")
            .joinpath("assets/office-cat-sprite.webp")
            .read_bytes()
        )
        return HttpResponse(data, content_type="image/webp")

    def post(self, request, public_id):
        context = self.context(request, public_id, "configure")
        upload = request.FILES.get("file")
        if not upload:
            raise AssistantError("Choose a PNG or WebP mascot image.")
        data = validated_asset(upload)
        config, _ = AssistantSettings.objects.get_or_create(tenant_id=context.tenant_id)
        config.mascot_asset = data
        config.save(update_fields=["mascot_asset"])
        return Response({"has_mascot_asset": True})
