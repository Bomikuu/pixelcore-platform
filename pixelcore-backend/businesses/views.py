import hashlib

import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .google_calendar import (
    GoogleCalendarError,
    build_google_authorization_url,
    decode_google_state,
    delete_google_event,
    exchange_authorization_code,
    save_google_connection,
    sync_calendar_event,
)
from .models import (
    AuditEvent,
    AccountProfile,
    Business,
    BusinessAsset,
    BusinessCard,
    BusinessEvent,
    BusinessDevice,
    DeviceLink,
    BusinessInvitation,
    BusinessLocation,
    BusinessMembership,
    GoogleCalendarConnection,
)
from .permissions import CanManageBusiness
from .serializers import (
    BusinessIdentitySerializer,
    AuditEventSerializer,
    BusinessAssetSerializer,
    BusinessCapabilitySerializer,
    BusinessEventSerializer,
    BusinessDeviceSerializer,
    DeviceLinkSerializer,
    BusinessInvitationSerializer,
    BusinessCardSerializer,
    BusinessLocationSerializer,
    MembershipSerializer,
    PublicBusinessIdentitySerializer,
    PublicBusinessCardSerializer,
    RegistrationSerializer,
    OnboardingSerializer,
)
from .services import consume_account_challenge, create_invitation, issue_account_challenge, issue_device_pairing_code, pair_device, record_audit, sync_enabled_modules
from .tasks import send_account_code, send_team_invitation


User = get_user_model()


def set_refresh_cookie(response, token):
    response.set_cookie(
        settings.PIXELCORE_REFRESH_COOKIE,
        str(token),
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=settings.PIXELCORE_COOKIE_SECURE,
        samesite=settings.PIXELCORE_COOKIE_SAMESITE,
        path="/api/auth/",
    )


def authenticated_response(user, status_code=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    response = Response(
        {
            "access": str(refresh.access_token),
            "needs_onboarding": not user.business_memberships.filter(status="active").exists(),
        },
        status=status_code,
    )
    set_refresh_cookie(response, refresh)
    return response


def deliver_account_code(user, purpose, code):
    try:
        send_account_code.delay(user.email, user.first_name, purpose, code)
    except Exception:
        send_account_code(user.email, user.first_name, purpose, code)


def deliver_team_invitation(invitation_id, token):
    try:
        send_team_invitation.delay(invitation_id, token)
    except Exception:
        send_team_invitation(invitation_id, token)


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, code = issue_account_challenge(user, "verify_email")
        deliver_account_code(user, "verify_email", code)
        return Response(
            {"id": user.id, "email": user.email, "next": "verify_email"},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        code = str(request.data.get("code", "")).strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user or not consume_account_challenge(user, "verify_email", code):
            return Response(
                {"error": {"code": "INVALID_VERIFICATION_CODE", "message": "The verification code is invalid or expired.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = True
        user.save(update_fields=["is_active"])
        profile, _ = AccountProfile.objects.get_or_create(user=user)
        profile.email_verified_at = timezone.now()
        profile.save(update_fields=["email_verified_at", "updated_at"])
        return authenticated_response(user)


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user:
            _, code = issue_account_challenge(user, "verify_email")
            deliver_account_code(user, "verify_email", code)
        return Response({"message": "If verification is pending, a new code has been sent."})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        identifier = str(request.data.get("identifier", "")).strip()
        user = find_user(identifier)
        if user and user.email:
            _, code = issue_account_challenge(user, "reset_password")
            deliver_account_code(user, "reset_password", code)
        return Response({"message": "If the account exists, a reset code has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        identifier = str(request.data.get("identifier", "")).strip()
        code = str(request.data.get("code", "")).strip()
        new_password = request.data.get("new_password", "")
        user = find_user(identifier)
        if not user:
            return Response(
                {"error": {"code": "INVALID_RESET_CODE", "message": "The reset code is invalid or expired.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(new_password, user)
        except Exception as exc:
            raise ValidationError({"new_password": list(getattr(exc, "messages", [str(exc)]))}) from exc
        if not consume_account_challenge(user, "reset_password", code):
            return Response(
                {"error": {"code": "INVALID_RESET_CODE", "message": "The reset code is invalid or expired.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"message": "Password updated. You can now sign in."})


def find_user(identifier):
    if not identifier:
        return None
    return (
        User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier))
        .first()
        or User.objects.filter(account_profile__phone=identifier).first()
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        identifier = str(request.data.get("identifier") or request.data.get("email") or "").strip()
        password = request.data.get("password", "")
        candidate = find_user(identifier)
        user = authenticate(request, username=candidate.username, password=password) if candidate else None
        if user is None or not user.is_active:
            return Response(
                {"error": {"code": "INVALID_CREDENTIALS", "message": "The account details are incorrect or verification is pending.", "details": {}}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return authenticated_response(user)


class GoogleAccountView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        credential = str(request.data.get("credential") or request.data.get("google_token") or "")
        client_id = settings.GOOGLE_IDENTITY_CLIENT_ID
        if not credential or not client_id:
            return Response(
                {"error": {"code": "GOOGLE_AUTH_UNAVAILABLE", "message": "Google sign-in is not configured.", "details": {}}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            token_info = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential},
                timeout=10,
            )
            token_info.raise_for_status()
            identity = token_info.json()
        except (requests.RequestException, ValueError):
            return Response(
                {"error": {"code": "INVALID_GOOGLE_CREDENTIAL", "message": "Google could not verify this sign-in.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if identity.get("aud") != client_id or identity.get("email_verified") not in (True, "true"):
            return Response(
                {"error": {"code": "INVALID_GOOGLE_CREDENTIAL", "message": "Google could not verify this sign-in.", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = str(identity.get("email", "")).strip().lower()
        if not email:
            raise ValidationError({"credential": "Google did not provide an email address."})
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": str(identity.get("given_name", ""))[:150],
                "last_name": str(identity.get("family_name", ""))[:150],
                "is_active": True,
            },
        )
        if not created and not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        profile, _ = AccountProfile.objects.get_or_create(user=user)
        if not profile.email_verified_at:
            profile.email_verified_at = timezone.now()
            profile.save(update_fields=["email_verified_at", "updated_at"])
        return authenticated_response(user)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        business = serializer.save()
        return Response(BusinessIdentitySerializer(business, context={"request": request}).data, status=status.HTTP_201_CREATED)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.PIXELCORE_REFRESH_COOKIE)
        if not raw_refresh:
            return Response(
                {"error": {"code": "REFRESH_REQUIRED", "message": "Sign in again to continue."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {"error": {"code": "REFRESH_INVALID", "message": "Your session has expired. Sign in again to continue."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response_data = {"access": serializer.validated_data["access"]}
        response = Response(response_data)
        rotated_refresh = serializer.validated_data.get("refresh")
        if rotated_refresh:
            set_refresh_cookie(response, rotated_refresh)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.PIXELCORE_REFRESH_COOKIE)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except Exception:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(settings.PIXELCORE_REFRESH_COOKIE, path="/api/auth/")
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = request.user.business_memberships.select_related("business").filter(status="active")
        from deliveries.services import has_delivery_access
        delivery_access = has_delivery_access(request.user)
        return Response(
            {
                "id": request.user.id,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "username": request.user.username,
                "phone": getattr(getattr(request.user, "account_profile", None), "phone", ""),
                "needs_onboarding": not memberships.exists() and not delivery_access,
                "has_delivery_access": delivery_access,
                "businesses": [
                    {
                        "public_id": str(membership.business.public_id),
                        "display_name": membership.business.display_name,
                        "slug": membership.business.slug,
                        "role": membership.role,
                    }
                    for membership in memberships
                ],
            }
        )


def business_card_defaults(user, business):
    membership = business.memberships.select_related("user").get(user=user, status="active")
    staff_profile = getattr(membership, "staff_profile", None)
    account_profile = getattr(user, "account_profile", None)
    business_socials = (business.branding or {}).get("socials", [])
    display_name = user.get_full_name().strip() or user.username or user.email.split("@", 1)[0]
    return {
        "display_name": display_name,
        "job_title": getattr(staff_profile, "job_title", "") or membership.get_role_display(),
        "headline": getattr(staff_profile, "bio", "")[:220] or business.tagline,
        "email": user.email,
        "phone": getattr(account_profile, "phone", "") or business.contact_phone,
        "social_links": business_socials[:4],
    }


class BusinessCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        card = BusinessCard.objects.select_related(
            "background_asset",
            "custom_font_asset",
        ).filter(
            business=business,
            user=request.user,
        ).first()
        if card:
            return Response(BusinessCardSerializer(card, context={"request": request}).data)

        draft = BusinessCard(
            business=business,
            user=request.user,
            **business_card_defaults(request.user, business),
        )
        data = BusinessCardSerializer(draft, context={"request": request}).data
        data["public_id"] = None
        return Response(data)

    @transaction.atomic
    def put(self, request, public_id):
        business = member_business(request.user, public_id)
        card = BusinessCard.objects.select_for_update().filter(
            business=business,
            user=request.user,
        ).first()
        created = card is None
        if created:
            card = BusinessCard(
                business=business,
                user=request.user,
                **business_card_defaults(request.user, business),
            )

        serializer = BusinessCardSerializer(
            card,
            data=request.data,
            partial=True,
            context={"request": request, "business": business},
        )
        serializer.is_valid(raise_exception=True)
        card = serializer.save(business=business, user=request.user)
        record_audit(
            business,
            request.user,
            "business_card.created" if created else "business_card.updated",
            "business_card",
            card.public_id,
            {"is_published": card.is_published, "style": card.style},
        )
        return Response(
            BusinessCardSerializer(card, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class BusinessCardBackgroundUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id)
        upload = request.FILES.get("file")
        serializer = BusinessAssetSerializer(
            data={
                "title": str(request.data.get("title", "Card background"))[:160],
                "alt_text": str(request.data.get("alt_text", ""))[:250],
                "asset_type": "image",
                "file": upload,
            },
            context={"business": business, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        asset = serializer.save()
        record_audit(
            business,
            request.user,
            "business_card.background_uploaded",
            "business_asset",
            asset.public_id,
        )
        return Response(
            BusinessAssetSerializer(asset, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class BusinessCardFontUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id)
        upload = request.FILES.get("file")
        serializer = BusinessAssetSerializer(
            data={
                "title": str(request.data.get("title", "Custom card font"))[:160],
                "alt_text": "",
                "asset_type": "font",
                "file": upload,
            },
            context={"business": business, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        asset = serializer.save()
        record_audit(
            business,
            request.user,
            "business_card.font_uploaded",
            "business_asset",
            asset.public_id,
        )
        return Response(
            BusinessAssetSerializer(asset, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PublicBusinessCardView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, public_id):
        card = get_object_or_404(
            BusinessCard.objects.select_related(
                "background_asset",
                "custom_font_asset",
                "business",
                "user",
            ),
            public_id=public_id,
            is_published=True,
            business__status="active",
        )
        return Response(PublicBusinessCardSerializer(card, context={"request": request}).data)


class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessIdentitySerializer
    lookup_field = "public_id"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Business.objects.all()
        return Business.objects.filter(
            memberships__user=self.request.user,
            memberships__status="active",
        ).distinct()

    def get_permissions(self):
        if self.action in {"partial_update", "identity"} and self.request.method == "PATCH":
            return [IsAuthenticated(), CanManageBusiness()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get", "patch"], url_path="identity")
    def identity(self, request, public_id=None):
        business = self.get_object()
        if request.method == "PATCH":
            self.check_object_permissions(request, business)
            serializer = self.get_serializer(business, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(self.get_serializer(business).data)

    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, public_id=None):
        business = self.get_object()
        memberships = business.memberships.select_related("user")
        return Response(MembershipSerializer(memberships, many=True).data)


class BusinessDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessDeviceSerializer
    lookup_field = "public_id"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_business(self):
        return member_business(self.request.user, self.kwargs["business_public_id"], roles=("owner", "admin", "manager"))

    def get_queryset(self):
        return BusinessDevice.objects.filter(business=self.get_business()).select_related("location")

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "business": self.get_business()}

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.token_version += 1
        instance.pairing_code_digest = ""
        instance.pairing_code_encrypted = ""
        instance.pairing_code_issued_at = None
        instance.save(update_fields=["is_active", "token_version", "pairing_code_digest", "pairing_code_encrypted", "pairing_code_issued_at", "updated_at"])

    @action(detail=True, methods=["get", "post"], url_path="pairing-code")
    def pairing_code(self, request, business_public_id=None, public_id=None):
        device = self.get_object()
        if request.method == "GET":
            from .services import current_device_pairing_code
            return Response({"pairing_code": current_device_pairing_code(device), "issued_at": device.pairing_code_issued_at})
        code = issue_device_pairing_code(device)
        record_audit(device.business, request.user, "device.pairing_code_issued", "business_device", device.public_id)
        return Response({"pairing_code": code, "expires_note": "This code is single-use and is replaced when a new code is generated."})


class DeviceLinkViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceLinkSerializer
    lookup_field = "public_id"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_business(self):
        return member_business(self.request.user, self.kwargs["business_public_id"], roles=("owner", "admin", "manager"))

    def get_queryset(self):
        return DeviceLink.objects.filter(business=self.get_business()).select_related("source_device", "target_device")

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "business": self.get_business()}

    def perform_destroy(self, instance):
        record_audit(instance.business, self.request.user, "device_link.deleted", "device_link", instance.public_id)
        instance.delete()


class DevicePairView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        requested_type = str(request.data.get("device_type", "")).strip()
        allowed_types = {requested_type} if requested_type else None
        device, token = pair_device(
            str(request.data.get("pairing_code", "")),
            allowed_types,
        )
        if not device:
            return Response({"error": {"code": "INVALID_PAIRING_CODE", "message": "The pairing code is invalid or has already been used.", "details": {}}}, status=400)
        return Response({"device_token": token, "device": BusinessDeviceSerializer(device).data})


class PublicBusinessIdentityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        business = Business.objects.filter(slug=slug, status="active").first()
        if business is None:
            return Response(
                {"error": {"code": "NOT_FOUND", "message": "Business identity was not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PublicBusinessIdentitySerializer(business, context={"request": request}).data)


def member_business(user, public_id, management=False, roles=None):
    allowed_roles = roles or (("owner", "admin") if management else ("owner", "admin", "manager", "staff"))
    return get_object_or_404(
        Business.objects.filter(
            public_id=public_id,
            memberships__user=user,
            memberships__status="active",
            memberships__role__in=allowed_roles,
        ).distinct()
    )


def paginated_response(request, queryset, serializer_class, page_size=20):
    paginator = PageNumberPagination()
    paginator.page_size = page_size
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_class(page, many=True, context={"request": request}).data)


class BusinessCapabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        return Response(BusinessCapabilitySerializer(business.capabilities.all(), many=True).data)

    def patch(self, request, public_id, code):
        business = member_business(request.user, public_id, management=True)
        if code == "smokey":
            from .models import BusinessCapability
            BusinessCapability.objects.get_or_create(business=business, code=code, defaults={"status": "disabled"})
        capability = get_object_or_404(business.capabilities, code=code)
        serializer = BusinessCapabilitySerializer(capability, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        sync_enabled_modules(business)
        record_audit(business, request.user, "capability.updated", "business_capability", code)
        return Response(serializer.data)


class BusinessLocationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        return paginated_response(request, business.locations.all(), BusinessLocationSerializer)

    def post(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        serializer = BusinessLocationSerializer(data=request.data, context={"business": business, "request": request})
        serializer.is_valid(raise_exception=True)
        location = serializer.save()
        record_audit(business, request.user, "location.created", "business_location", location.public_id)
        return Response(BusinessLocationSerializer(location).data, status=status.HTTP_201_CREATED)


class BusinessLocationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, public_id, location_id, management=False):
        business = member_business(request.user, public_id, management=management)
        return get_object_or_404(BusinessLocation, business=business, public_id=location_id)

    def get(self, request, public_id, location_id):
        return Response(BusinessLocationSerializer(self.get_object(request, public_id, location_id)).data)

    def patch(self, request, public_id, location_id):
        location = self.get_object(request, public_id, location_id, management=True)
        serializer = BusinessLocationSerializer(location, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        location = serializer.save()
        record_audit(location.business, request.user, "location.updated", "business_location", location.public_id)
        return Response(serializer.data)


class BusinessAssetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        return paginated_response(request, business.assets.all(), BusinessAssetSerializer)

    def post(self, request, public_id):
        business = member_business(request.user, public_id, roles=("owner", "admin", "manager"))
        serializer = BusinessAssetSerializer(data=request.data, context={"business": business, "request": request})
        serializer.is_valid(raise_exception=True)
        asset = serializer.save()
        record_audit(business, request.user, "asset.uploaded", "business_asset", asset.public_id)
        return Response(BusinessAssetSerializer(asset, context={"request": request}).data, status=status.HTTP_201_CREATED)


class BusinessInvitationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        return paginated_response(request, business.invitations.all(), BusinessInvitationSerializer)

    def post(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        serializer = BusinessInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, token = create_invitation(
            business,
            serializer.validated_data["email"],
            serializer.validated_data["role"],
            request.user,
        )
        transaction.on_commit(
            lambda: deliver_team_invitation(invitation.id, token)
        )
        return Response(BusinessInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class BusinessEmployeeInvitationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        from scheduling.models import StaffProfile
        from scheduling.serializers import StaffProfileSerializer

        business = member_business(request.user, public_id, management=True)
        email = str(request.data.get("email", "")).strip().lower()
        role = str(request.data.get("role", "staff")).strip().lower()
        creation_mode = str(request.data.get("creation_mode", "manual")).strip().lower()
        if not email:
            raise ValidationError(
                {"email": "A work email is required to send the employee invitation."}
            )
        if role not in {"admin", "manager", "staff"}:
            raise ValidationError(
                {"role": "Choose administrator, manager, or staff access."}
            )
        if creation_mode not in {"manual", "invite"}:
            raise ValidationError(
                {"creation_mode": "Choose manual creation or email invitation."}
            )
        if StaffProfile.objects.filter(
            business=business,
            email__iexact=email,
        ).exists():
            raise ValidationError(
                {"email": "An employee profile already uses this email."}
            )
        if BusinessMembership.objects.filter(
            business=business,
            user__email__iexact=email,
            status="active",
        ).exists():
            raise ValidationError(
                {"email": "This person already belongs to the business."}
            )

        if creation_mode == "invite":
            email_name = email.partition("@")[0].replace(".", " ").replace("_", " ")
            employee_data = {
                "display_name": email_name.title() or "Invited employee",
                "email": email,
                "employment_status": "pending",
                "timezone": business.timezone,
                "is_bookable": False,
                "is_active": True,
            }
        else:
            employee_data = request.data.copy()
            employee_data.pop("role", None)
            employee_data.pop("membership_id", None)
            employee_data.pop("creation_mode", None)
            employee_data["email"] = email
            employee_data["employment_status"] = "pending"
            employee_data["is_active"] = True
        serializer = StaffProfileSerializer(
            data=employee_data,
            context={"business": business, "request": request},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            staff = serializer.save(business=business)
            BusinessInvitation.objects.filter(
                business=business,
                email__iexact=email,
                status="pending",
            ).update(status="revoked")
            invitation, token = create_invitation(
                business,
                email,
                role,
                request.user,
            )
            transaction.on_commit(
                lambda: deliver_team_invitation(invitation.id, token)
            )

        return Response(
            {
                "employee": StaffProfileSerializer(
                    staff,
                    context={"business": business, "request": request},
                ).data,
                "invitation": BusinessInvitationSerializer(invitation).data,
                "creation_mode": creation_mode,
            },
            status=status.HTTP_201_CREATED,
        )


class BusinessInvitationValidateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def get(self, request):
        invitation = invitation_from_token(request.query_params.get("token"))
        if not invitation:
            return invitation_unavailable_response()
        return Response(invitation_registration_payload(invitation))


class BusinessInvitationRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        token = str(request.data.get("token", ""))
        digest = hashlib.sha256(token.encode()).hexdigest()

        with transaction.atomic():
            invitation = (
                BusinessInvitation.objects.select_for_update()
                .select_related("business")
                .filter(token_digest=digest, status="pending")
                .first()
            )
            if not invitation or invitation.is_expired:
                if invitation:
                    invitation.status = "expired"
                    invitation.save(update_fields=["status"])
                return invitation_unavailable_response()

            existing_user = User.objects.filter(
                email__iexact=invitation.email
            ).first()
            if existing_user:
                return Response(
                    {
                        "error": {
                            "code": "ACCOUNT_EXISTS",
                            "message": (
                                "An account already uses this email. "
                                "Sign in to accept the invitation."
                            ),
                            "details": {},
                        }
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            registration_data = {
                field: request.data.get(field, "")
                for field in (
                    "first_name",
                    "last_name",
                    "phone",
                    "username",
                    "password",
                    "password_confirm",
                )
            }
            registration_data["email"] = invitation.email
            serializer = RegistrationSerializer(data=registration_data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            user.is_active = True
            user.save(update_fields=["is_active"])

            profile = user.account_profile
            profile.email_verified_at = timezone.now()
            profile.save(update_fields=["email_verified_at", "updated_at"])

            membership, _ = BusinessMembership.objects.update_or_create(
                business=invitation.business,
                user=user,
                defaults={"role": invitation.role, "status": "active"},
            )
            from scheduling.models import StaffProfile

            staff = StaffProfile.objects.filter(
                business=invitation.business,
                email__iexact=invitation.email,
            ).first()
            if staff:
                staff.membership = membership
                staff.display_name = user.get_full_name() or staff.display_name
                staff.job_title = str(
                    request.data.get("job_title", staff.job_title)
                ).strip()[:120]
                staff.emergency_contact_name = str(
                    request.data.get(
                        "emergency_contact_name",
                        staff.emergency_contact_name,
                    )
                ).strip()[:160]
                staff.emergency_contact_phone = str(
                    request.data.get(
                        "emergency_contact_phone",
                        staff.emergency_contact_phone,
                    )
                ).strip()[:32]
                staff.save(
                    update_fields=[
                        "membership",
                        "display_name",
                        "job_title",
                        "emergency_contact_name",
                        "emergency_contact_phone",
                        "updated_at",
                    ]
                )
            else:
                StaffProfile.objects.create(
                    business=invitation.business,
                    membership=membership,
                    display_name=user.get_full_name() or user.email,
                    email=user.email,
                    job_title=str(request.data.get("job_title", "")).strip()[:120],
                    emergency_contact_name=str(
                        request.data.get("emergency_contact_name", "")
                    ).strip()[:160],
                    emergency_contact_phone=str(
                        request.data.get("emergency_contact_phone", "")
                    ).strip()[:32],
                    employment_status="pending",
                    timezone=invitation.business.timezone,
                    is_bookable=False,
                )

            invitation.status = "accepted"
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["status", "accepted_at"])
            record_audit(
                invitation.business,
                user,
                "team.invitation_registered",
                "business_invitation",
                invitation.public_id,
            )

        return authenticated_response(user, status.HTTP_201_CREATED)


def invitation_from_token(raw_token):
    token = str(raw_token or "")
    if not token:
        return None
    digest = hashlib.sha256(token.encode()).hexdigest()
    invitation = (
        BusinessInvitation.objects.select_related("business")
        .filter(token_digest=digest, status="pending")
        .first()
    )
    if not invitation or invitation.is_expired:
        if invitation:
            invitation.status = "expired"
            invitation.save(update_fields=["status"])
        return None
    return invitation


def invitation_registration_payload(invitation):
    business = invitation.business
    staff = business.staff_profiles.filter(
        email__iexact=invitation.email
    ).first()
    return {
        "business": {
            "display_name": business.display_name,
            "logo_url": business.logo.url if business.logo else None,
            "industry_preset": business.industry_preset,
        },
        "email": invitation.email,
        "role": invitation.role,
        "job_title": staff.job_title if staff else "",
        "employee_name": staff.display_name if staff else "",
        "emergency_contact_name": staff.emergency_contact_name if staff else "",
        "emergency_contact_phone": staff.emergency_contact_phone if staff else "",
        "profile_is_prefilled": bool(
            staff
            and (
                staff.job_title
                or staff.emergency_contact_name
                or staff.emergency_contact_phone
                or staff.hired_at
            )
        ),
        "expires_at": invitation.expires_at,
        "account_exists": User.objects.filter(
            email__iexact=invitation.email
        ).exists(),
    }


def invitation_unavailable_response():
    return Response(
        {
            "error": {
                "code": "INVITATION_UNAVAILABLE",
                "message": (
                    "This invitation is invalid, expired, or has already been used."
                ),
                "details": {},
            }
        },
        status=status.HTTP_410_GONE,
    )


class BusinessInvitationAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = str(request.data.get("token", ""))
        digest = hashlib.sha256(token.encode()).hexdigest()
        invitation = get_object_or_404(BusinessInvitation, token_digest=digest, status="pending")
        if invitation.is_expired:
            invitation.status = "expired"
            invitation.save(update_fields=["status"])
            return Response(
                {"error": {"code": "INVITATION_EXPIRED", "message": "This invitation has expired.", "details": {}}},
                status=status.HTTP_410_GONE,
            )
        if request.user.email.lower() != invitation.email.lower():
            return Response(
                {"error": {"code": "EMAIL_MISMATCH", "message": "Sign in with the invited email address.", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        membership, _ = BusinessMembership.objects.update_or_create(
            business=invitation.business,
            user=request.user,
            defaults={"role": invitation.role, "status": "active"},
        )
        from scheduling.models import StaffProfile
        staff = StaffProfile.objects.filter(business=invitation.business, email__iexact=request.user.email).first()
        if staff:
            staff.membership = membership
            staff.save(update_fields=["membership", "updated_at"])
        else:
            StaffProfile.objects.create(
                business=invitation.business,
                membership=membership,
                display_name=request.user.get_full_name() or request.user.email,
                email=request.user.email,
                employment_status="pending",
                timezone=invitation.business.timezone,
                is_bookable=False,
            )
        invitation.status = "accepted"
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at"])
        record_audit(invitation.business, request.user, "team.invitation_accepted", "business_invitation", invitation.public_id)
        return Response(BusinessInvitationSerializer(invitation).data)


class BusinessAuditEventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        queryset = AuditEvent.objects.filter(business=business).select_related("actor")
        return paginated_response(request, queryset, AuditEventSerializer, page_size=50)


class BusinessEventListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id)
        events = business.events.all()
        starts_after = request.query_params.get("starts_after")
        starts_before = request.query_params.get("starts_before")
        if starts_after:
            parsed_start = parse_datetime(starts_after)
            if parsed_start is None:
                raise ValidationError({"starts_after": "Use an ISO 8601 date and time."})
            events = events.filter(starts_at__gte=parsed_start)
        if starts_before:
            parsed_end = parse_datetime(starts_before)
            if parsed_end is None:
                raise ValidationError({"starts_before": "Use an ISO 8601 date and time."})
            events = events.filter(starts_at__lte=parsed_end)
        paginator = PageNumberPagination()
        paginator.page_size = 50
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(BusinessEventSerializer(page, many=True).data)

    def post(self, request, public_id):
        business = member_business(request.user, public_id)
        serializer = BusinessEventSerializer(data=request.data, context={"business": business})
        serializer.is_valid(raise_exception=True)
        event = serializer.save(business=business, created_by=request.user)
        sync_calendar_event(event)
        return Response(BusinessEventSerializer(event).data, status=status.HTTP_201_CREATED)


class BusinessEventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_event(self, request, public_id, event_id):
        business = member_business(request.user, public_id)
        return get_object_or_404(BusinessEvent, id=event_id, business=business)

    def get(self, request, public_id, event_id):
        return Response(BusinessEventSerializer(self.get_event(request, public_id, event_id)).data)

    def patch(self, request, public_id, event_id):
        event = self.get_event(request, public_id, event_id)
        serializer = BusinessEventSerializer(event, data=request.data, partial=True, context={"business": event.business})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        sync_calendar_event(event)
        return Response(BusinessEventSerializer(event).data)

    def delete(self, request, public_id, event_id):
        event = self.get_event(request, public_id, event_id)
        delete_google_event(event)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleCalendarConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        connection = GoogleCalendarConnection.objects.filter(business=business).first()
        if connection and connection.is_active:
            return Response(
                {
                    "connected": True,
                    "google_email": connection.google_email,
                    "last_synced_at": connection.last_synced_at,
                    "last_error": connection.last_error,
                }
            )
        try:
            authorize_url = build_google_authorization_url(request.user, business)
        except GoogleCalendarError as exc:
            authorize_url = ""
            configuration_error = str(exc)
        else:
            configuration_error = ""
        return Response(
            {
                "connected": False,
                "authorize_url": authorize_url,
                "configuration_error": configuration_error,
            }
        )

    def delete(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        GoogleCalendarConnection.objects.filter(business=business).delete()
        business.events.update(
            google_sync_status="not_connected",
            google_sync_error="",
            google_event_id="",
            google_event_url="",
            google_calendar_id="",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleCalendarCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            state_payload = decode_google_state(request.query_params.get("state", ""))
            user = get_object_or_404(User, id=state_payload["user_id"], is_active=True)
            business = get_object_or_404(Business, id=state_payload["business_id"])
            if not business.memberships.filter(
                user=user,
                status="active",
                role__in=("owner", "admin"),
            ).exists():
                raise GoogleCalendarError("This account can no longer manage the selected business.")
            token_payload = exchange_authorization_code(request.query_params.get("code", ""))
            connection = save_google_connection(business, user, token_payload)
            for event in business.events.all()[:500]:
                sync_calendar_event(event, connection)
            connection.last_synced_at = timezone.now()
            connection.save(update_fields=["last_synced_at", "updated_at"])
            return redirect(f"{settings.PIXELCORE_FRONTEND_URL}/settings/integrations?google=connected")
        except (GoogleCalendarError, KeyError):
            return redirect(f"{settings.PIXELCORE_FRONTEND_URL}/settings/integrations?google=error")


class GoogleCalendarSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        business = member_business(request.user, public_id, management=True)
        connection = get_object_or_404(GoogleCalendarConnection, business=business, is_active=True)
        synced = 0
        for event in business.events.all()[:500]:
            synced += int(sync_calendar_event(event, connection))
        connection.last_synced_at = timezone.now()
        connection.save(update_fields=["last_synced_at", "updated_at"])
        return Response({"synced": synced, "total": business.events.count()})
