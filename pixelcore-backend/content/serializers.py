import re
import secrets

from rest_framework import serializers

from businesses.serializers import PublicBusinessIdentitySerializer
from .blocks import SAFE_PATH, validate_page_content
from .models import PageRevision, Site, SiteDomain, SitePage


HOSTNAME = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["public_id", "name", "status", "navigation", "settings", "cache_version", "published_at", "created_at", "updated_at"]
        read_only_fields = ["public_id", "status", "cache_version", "published_at", "created_at", "updated_at"]

    def validate_navigation(self, value):
        if not isinstance(value, list) or len(value) > 20:
            raise serializers.ValidationError("Navigation must contain at most 20 items.")
        for item in value:
            if set(item) - {"id", "label", "path", "children"}:
                raise serializers.ValidationError("Navigation contains unsupported fields.")
            if not str(item.get("label", "")).strip() or not SAFE_PATH.fullmatch(str(item.get("path", ""))):
                raise serializers.ValidationError("Navigation labels and internal paths are required.")
        return value


class PageRevisionSerializer(serializers.ModelSerializer):
    created_by = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = PageRevision
        fields = ["public_id", "number", "schema_version", "content", "checksum", "created_by", "created_at"]
        read_only_fields = ["public_id", "number", "schema_version", "checksum", "created_by", "created_at"]

    def validate_content(self, value):
        return validate_page_content(value)


class SitePageSerializer(serializers.ModelSerializer):
    draft_revision = PageRevisionSerializer(read_only=True)
    published_revision = PageRevisionSerializer(read_only=True)

    class Meta:
        model = SitePage
        fields = [
            "public_id", "title", "slug", "page_type", "status", "seo_title", "seo_description", "no_index",
            "draft_revision", "published_revision", "published_at", "created_at", "updated_at",
        ]
        read_only_fields = ["public_id", "status", "draft_revision", "published_revision", "published_at", "created_at", "updated_at"]


class SiteDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteDomain
        fields = ["public_id", "hostname", "is_platform_subdomain", "verification_token", "verified_at", "is_active", "created_at"]
        read_only_fields = ["public_id", "is_platform_subdomain", "verification_token", "verified_at", "is_active", "created_at"]

    def validate_hostname(self, value):
        value = value.lower().strip().rstrip(".")
        if not HOSTNAME.fullmatch(value):
            raise serializers.ValidationError("Enter a valid hostname without a scheme or path.")
        return value

    def create(self, validated_data):
        return SiteDomain.objects.create(verification_token=secrets.token_urlsafe(24), **validated_data)


class PublicSiteManifestSerializer(serializers.Serializer):
    identity = PublicBusinessIdentitySerializer()
    site = serializers.DictField()
    page = serializers.DictField()
    seo = serializers.DictField()

