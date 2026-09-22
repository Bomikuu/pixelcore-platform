import hmac

import dns.resolver
from django.conf import settings
from django.core import signing
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.models import Business, BusinessAsset
from businesses.serializers import PublicBusinessIdentitySerializer
from businesses.services import record_audit
from businesses.views import member_business, paginated_response
from catalog.models import Offering
from .models import PageRevision, Site, SiteDomain, SitePage
from .serializers import PageRevisionSerializer, SiteDomainSerializer, SitePageSerializer, SiteSerializer
from .services import create_revision, make_preview_token, publish_revision, read_preview_token
from .hero import hero_asset_ids


def get_or_create_site(business):
    site, _ = Site.objects.get_or_create(business=business, defaults={"name": business.display_name})
    hostname = f"{business.slug}.{settings.PIXELCORE_PLATFORM_DOMAIN}".lower()
    SiteDomain.objects.get_or_create(
        site=site,
        hostname=hostname,
        defaults={"is_platform_subdomain": True, "verified_at": timezone.now(), "is_active": True},
    )
    return site


class SiteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        return Response(SiteSerializer(get_or_create_site(business)).data)

    def patch(self, request, public_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        site = get_or_create_site(business)
        serializer = SiteSerializer(site, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit(business, request.user, "site.updated", "site", site.public_id)
        return Response(serializer.data)


class CommerceTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        site = get_or_create_site(business)
        home = site.pages.filter(page_type="home").first()
        if home and home.published_revision_id and not request.data.get("confirm_replace"):
            return Response({"error": {"code": "PUBLISHED_HOME_EXISTS", "message": "Confirm before replacing the home page draft with the commerce template.", "details": {"page_public_id": str(home.public_id)}}}, status=409)
        if home is None:
            home = SitePage.objects.create(site=site, title="Home", slug="home", page_type="home")
        featured = list(business.offerings.filter(status="published").exclude(offering_type="service").order_by("-created_at")[:8])
        lead = featured[0] if featured else None
        content = {"schema_version": 1, "blocks": [
            {"id": "commerce-hero", "type": "commerce_hero", "version": 1, "settings": {"heading": lead.name if lead else business.display_name, "body": lead.summary if lead else (business.tagline or "Explore our latest products."), "offering_id": str(lead.public_id) if lead else "", "primary_label": "Shop now", "primary_path": "/shop", "secondary_label": "Explore collections", "secondary_path": "/shop"}},
            {"id": "new-arrivals", "type": "product_rail", "version": 1, "settings": {"heading": "New arrivals", "offering_ids": [str(item.public_id) for item in featured], "limit": 8}},
            {"id": "commerce-values", "type": "policy_highlights", "version": 1, "settings": {"items": [{"heading": "Secure checkout", "body": "Payments and totals are confirmed by the business server."}, {"heading": "Clear fulfillment", "body": "Delivery, pickup, and digital options appear when available."}, {"heading": "Business support", "body": "Contact details come directly from this storefront."}]}},
        ]}
        revision = create_revision(home, content, request.user)
        navigation = [item for item in site.navigation if item.get("path") != "/shop"]
        site.navigation = [{"id": "shop", "label": "Shop", "path": "/shop"}, *navigation]
        site.settings = {**site.settings, "template": "commerce"}
        site.save(update_fields=["navigation", "settings", "updated_at"])
        record_audit(business, request.user, "site.commerce_template_applied", "site_page", home.public_id)
        home.refresh_from_db()
        return Response({"page": SitePageSerializer(home).data, "revision": PageRevisionSerializer(revision).data})


class SitePageListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        return paginated_response(request, get_or_create_site(business).pages.all(), SitePageSerializer)

    def post(self, request, public_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        site = get_or_create_site(business)
        serializer = SitePageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        page = serializer.save(site=site)
        content = request.data.get("content", {"schema_version": 1, "blocks": []})
        create_revision(page, content, request.user)
        page.refresh_from_db()
        record_audit(business, request.user, "site.page_created", "site_page", page.public_id)
        return Response(SitePageSerializer(page).data, status=status.HTTP_201_CREATED)


class SitePageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_page(self, request, public_id, page_id, mutate=False):
        roles = ("owner", "admin", "manager") if mutate else None
        business = member_business(request.user, public_id, roles=roles)
        return get_object_or_404(SitePage.objects.select_related("site", "draft_revision", "published_revision"), site__business=business, public_id=page_id)

    def get(self, request, public_id, page_id):
        return Response(SitePageSerializer(self.get_page(request, public_id, page_id)).data)

    def patch(self, request, public_id, page_id):
        page = self.get_page(request, public_id, page_id, mutate=True)
        serializer = SitePageSerializer(page, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if "content" in request.data:
            create_revision(page, request.data["content"], request.user)
        page.refresh_from_db()
        return Response(SitePageSerializer(page).data)

    def delete(self, request, public_id, page_id):
        page = self.get_page(request, public_id, page_id, mutate=True)
        record_audit(page.site.business, request.user, "site.page_deleted", "site_page", page.public_id)
        page.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageRevisionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get_page(self, request, public_id, page_id, mutate=False):
        roles = ("owner", "admin", "manager") if mutate else None
        business = member_business(request.user, public_id, roles=roles)
        return get_object_or_404(SitePage, site__business=business, public_id=page_id)

    def get(self, request, public_id, page_id):
        page = self.get_page(request, public_id, page_id)
        return paginated_response(request, page.revisions.all(), PageRevisionSerializer)

    def post(self, request, public_id, page_id):
        page = self.get_page(request, public_id, page_id, mutate=True)
        revision = create_revision(page, request.data.get("content"), request.user)
        return Response(PageRevisionSerializer(revision).data, status=status.HTTP_201_CREATED)


class PagePublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, page_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        page = get_object_or_404(SitePage, site__business=business, public_id=page_id)
        revision_id = request.data.get("revision_public_id")
        revision = get_object_or_404(PageRevision, page=page, public_id=revision_id) if revision_id else page.draft_revision
        if revision is None:
            raise ValidationError({"revision_public_id": "Create a revision before publishing."})
        publish_revision(page, revision, request.user)
        page.refresh_from_db()
        return Response(SitePageSerializer(page).data)


class PagePreviewTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, page_id):
        business = member_business(request.user, public_id)
        page = get_object_or_404(SitePage, site__business=business, public_id=page_id)
        revision = page.draft_revision
        if revision is None:
            raise ValidationError({"page": "This page has no draft revision."})
        token = make_preview_token(page, revision)
        return Response({"token": token, "expires_in": 3600, "robots": "noindex,nofollow"})


class SiteDomainListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        return Response(SiteDomainSerializer(get_or_create_site(business).domains.all(), many=True).data)

    def post(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        site = get_or_create_site(business)
        serializer = SiteDomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.save(site=site)
        record_audit(business, request.user, "site.domain_created", "site_domain", domain.public_id)
        return Response(SiteDomainSerializer(domain).data, status=status.HTTP_201_CREATED)


class SiteDomainVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id, domain_id):
        business = member_business(request.user, public_id, management=True)
        domain = get_object_or_404(SiteDomain, site__business=business, public_id=domain_id)
        expected = f"pixelcore-verification={domain.verification_token}"
        try:
            answers = dns.resolver.resolve(f"_pixelcore.{domain.hostname}", "TXT", lifetime=5)
            values = {b"".join(answer.strings).decode() for answer in answers}
        except Exception:
            values = set()
        if expected not in values:
            return Response(
                {"error": {"code": "DNS_NOT_VERIFIED", "message": "The required DNS TXT record was not found.", "details": {"record": f"_pixelcore.{domain.hostname}", "value": expected}}},
                status=status.HTTP_409_CONFLICT,
            )
        domain.verified_at = timezone.now()
        domain.is_active = True
        domain.save(update_fields=["verified_at", "is_active"])
        return Response(SiteDomainSerializer(domain).data)


def manifest_response(request, page, preview=False):
    revision = page.draft_revision if preview else page.published_revision
    if revision is None:
        return Response({"error": {"code": "NOT_FOUND", "message": "Published page not found.", "details": {}}}, status=404)
    business = page.site.business
    canonical_host = page.site.domains.filter(is_active=True, verified_at__isnull=False).values_list("hostname", flat=True).first()
    canonical_base = f"https://{canonical_host}" if canonical_host else f"{settings.PIXELCORE_FRONTEND_URL}/site/{business.slug}"
    path = "/" if page.page_type == "home" else f"/{page.slug}"
    asset_ids = set()
    offering_ids = set()
    for block in revision.content.get("blocks", []):
        settings_data = block.get("settings", {})
        asset_ids.update(hero_asset_ids(settings_data.get('slides', [])))
        for key in ("asset_id", "poster_asset_id"):
            if settings_data.get(key):
                asset_ids.add(str(settings_data[key]))
        asset_ids.update(str(value) for value in settings_data.get("asset_ids", []))
        asset_ids.update(str(item["asset_id"]) for item in settings_data.get("items", []) if isinstance(item, dict) and item.get("asset_id"))
        if settings_data.get("offering_id"):
            offering_ids.add(str(settings_data["offering_id"]))
        offering_ids.update(str(value) for value in settings_data.get("offering_ids", []))
    assets = BusinessAsset.objects.filter(business=business, public_id__in=asset_ids, processing_status='ready')
    offerings = Offering.objects.filter(business=business, status="published", public_id__in=offering_ids).select_related("product_profile").prefetch_related("ordered_media__asset", "variant_dimensions__values", "variants__option_values")
    graph = [{"@type": "Organization", "@id": f"{canonical_base}/#organization", "name": business.display_name, "url": canonical_base}]
    for offering in offerings:
        schema_type = "Service" if offering.offering_type == "service" else "Product"
        node = {
            "@type": schema_type,
            "name": offering.name,
            "description": offering.summary or offering.description[:300],
            "url": f"{canonical_base}/{'services' if schema_type == 'Service' else 'product'}/{offering.slug}",
        }
        if schema_type == "Product":
            node["offers"] = {
                "@type": "Offer",
                "price": str(offering.base_price),
                "priceCurrency": business.currency,
                "availability": "https://schema.org/InStock",
            }
        graph.append(node)
    payload = {
        "identity": PublicBusinessIdentitySerializer(business, context={"request": request}).data,
        "site": {"public_id": str(page.site.public_id), "name": page.site.name, "navigation": page.site.navigation, "settings": page.site.settings, "cache_version": page.site.cache_version},
        "page": {"public_id": str(page.public_id), "title": page.title, "slug": page.slug, "page_type": page.page_type, "content": revision.content, "revision": revision.number},
        "assets": [
            {"public_id": str(asset.public_id), "url": asset.file.url, "alt_text": asset.alt_text, "asset_type": asset.asset_type}
            for asset in assets
        ],
        "seo": {
            "title": page.seo_title or f"{page.title} | {business.display_name}",
            "description": page.seo_description or business.description[:180],
            "canonical": f"{canonical_base}{path}",
            "robots": "noindex,nofollow" if preview or page.no_index else "index,follow",
            "json_ld": {"@context": "https://schema.org", "@graph": graph},
        },
    }
    return Response(payload)


def _active_domain(request):
    hostname = request.META.get("HTTP_HOST", "").split(":", 1)[0].lower().rstrip(".")
    return SiteDomain.objects.select_related("site__business").filter(
        hostname=hostname,
        is_active=True,
        verified_at__isnull=False,
        site__business__status="active",
    ).first()


class PublicSitemapView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        domain = _active_domain(request)
        if domain is None:
            return HttpResponse(status=404)
        urls = []
        for page in domain.site.pages.filter(status="published", no_index=False).order_by("id"):
            path = "" if page.page_type == "home" else f"/{page.slug}"
            urls.append(f"<url><loc>https://{domain.hostname}{path}</loc></url>")
        body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(urls) + "</urlset>"
        return HttpResponse(body, content_type="application/xml")


class PublicRobotsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        domain = _active_domain(request)
        if domain is None:
            return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")
        body = f"User-agent: *\nAllow: /\nSitemap: https://{domain.hostname}/sitemap.xml\n"
        return HttpResponse(body, content_type="text/plain")


class PublicSiteManifestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, page_slug=None):
        page_filter = {"page_type": "home"} if not page_slug else {"slug": page_slug}
        page = get_object_or_404(
            SitePage.objects.select_related("site__business", "published_revision"),
            site__business__slug=slug,
            site__business__status="active",
            status="published",
            **page_filter,
        )
        return manifest_response(request, page)


class PublicPagePreviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            payload = read_preview_token(request.query_params.get("token", ""))
        except signing.BadSignature:
            return Response({"error": {"code": "INVALID_PREVIEW", "message": "This preview link is invalid or expired.", "details": {}}}, status=404)
        page = get_object_or_404(SitePage.objects.select_related("site__business", "draft_revision"), public_id=payload["page"], draft_revision__public_id=payload["revision"])
        return manifest_response(request, page, preview=True)


class PublicHostManifestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        hostname = request.query_params.get("host", "").split(":", 1)[0].lower().rstrip(".")
        requested_path = request.query_params.get("path", "/").strip("/")
        domain = get_object_or_404(
            SiteDomain.objects.select_related("site__business"),
            hostname=hostname,
            is_active=True,
            verified_at__isnull=False,
            site__business__status="active",
        )
        page_filter = {"page_type": "home"} if not requested_path else {"slug": requested_path}
        page = get_object_or_404(SitePage.objects.select_related("site__business", "published_revision"), site=domain.site, status="published", **page_filter)
        return manifest_response(request, page)


class InternalDomainAuthorizationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        supplied = request.headers.get("X-PixelCore-Domain-Key", "") or request.query_params.get("key", "")
        expected = settings.PIXELCORE_CADDY_AUTH_TOKEN
        if not expected or not hmac.compare_digest(supplied, expected):
            return Response(status=status.HTTP_403_FORBIDDEN)
        hostname = request.query_params.get("domain", "").lower().rstrip(".")
        allowed = SiteDomain.objects.filter(hostname=hostname, is_active=True, verified_at__isnull=False).exists()
        return Response(status=status.HTTP_204_NO_CONTENT if allowed else status.HTTP_404_NOT_FOUND)
