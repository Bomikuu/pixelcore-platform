from decimal import Decimal

from rest_framework import serializers
from smokey_assistant.providers import PROVIDERS


class ConnectionSerializer(serializers.Serializer):
    credits_usd = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        allow_null=True,
        required=False,
    )
    name = serializers.CharField(max_length=100)
    provider = serializers.ChoiceField(choices=list(PROVIDERS))
    model = serializers.CharField(max_length=180)
    permitted_models = serializers.ListField(
        child=serializers.CharField(max_length=180), max_length=40
    )
    secret = serializers.CharField(
        max_length=1000, write_only=True, required=False, trim_whitespace=True
    )


class SettingsSerializer(serializers.Serializer):
    default_connection_id = serializers.UUIDField(allow_null=True, required=False)
    presentation = serializers.ChoiceField(choices=["drawer", "modal"], required=False)
    mascot = serializers.JSONField(required=False)
    daily_requests = serializers.IntegerField(
        min_value=1, max_value=100000, required=False
    )
    monthly_requests = serializers.IntegerField(
        min_value=1, max_value=1000000, required=False
    )
    daily_tokens = serializers.IntegerField(
        min_value=1000, max_value=1000000000, required=False
    )
    monthly_tokens = serializers.IntegerField(
        min_value=1000, max_value=1000000000, required=False
    )

    def validate_mascot(self, value):
        if not isinstance(value, dict) or set(value) - {
            "mode",
            "asset_type",
            "columns",
            "rows",
            "frames",
        }:
            raise serializers.ValidationError(
                "Choose a supported mascot configuration."
            )
        if value.get("mode", "smokey") not in {
            "smokey",
            "custom",
            "standard",
        } or value.get("asset_type", "static") not in {"static", "sprite"}:
            raise serializers.ValidationError("Choose a valid mascot and asset type.")
        for key in ("columns", "rows"):
            if type(value.get(key, 1)) is not int or not 1 <= value.get(key, 1) <= 32:
                raise serializers.ValidationError(
                    "Sprite dimensions must be from 1 to 32."
                )
        frames = value.get("frames", {})
        if not isinstance(frames, dict) or set(frames) - {
            "idle",
            "searching",
            "generating",
            "success",
            "empty",
            "error",
            "cancelled",
        }:
            raise serializers.ValidationError("Invalid sprite states.")
        for frame in frames.values():
            if (
                not isinstance(frame, list)
                or len(frame) != 2
                or any(type(v) is not int for v in frame)
                or not 0 <= frame[0] < value.get("columns", 1)
                or not 0 <= frame[1] < value.get("rows", 1)
            ):
                raise serializers.ValidationError("A sprite frame is outside its grid.")
        return value
