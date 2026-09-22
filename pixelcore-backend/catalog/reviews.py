"""Public, paginated product reviews and account-owned review editing."""

from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from commerce.models import OrderItem
from .models import Offering, ProductReview


def published_product(slug, offering_slug):
    return get_object_or_404(
        Offering,
        business__slug=slug,
        business__status="active",
        slug=offering_slug,
        status="published",
    )


def has_purchase(user, product):
    # Only an already-linked customer account can prove ownership. Never trust
    # an email or order number supplied by the review request.
    return OrderItem.objects.filter(
        offering=product,
        order__business_id=product.business_id,
        order__customer__business_id=product.business_id,
        order__customer__user=user,
        order__payment_status__in=["paid", "partially_refunded"],
    ).exclude(order__status="cancelled").exists()


def review_summary(product):
    reviews = product.reviews.filter(is_visible=True)
    totals = reviews.aggregate(count=Count("id"), average=Avg("rating"))
    counts = dict(reviews.values_list("rating").annotate(total=Count("id")).order_by())
    return {
        "count": totals["count"],
        "average": round(totals["average"], 1) if totals["average"] is not None else None,
        "distribution": [{"rating": rating, "count": counts.get(rating, 0)} for rating in range(5, 0, -1)],
    }


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ["public_id", "author_name", "rating", "title", "body", "verified_purchase", "created_at", "updated_at"]
        read_only_fields = ["public_id", "author_name", "verified_purchase", "created_at", "updated_at"]

    def get_author_name(self, review):
        return review.author.first_name.strip() or "Customer"


class ReviewPagination(PageNumberPagination):
    page_size = 5


class ProductReviewsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, offering_slug):
        product = published_product(slug, offering_slug)
        reviews = product.reviews.filter(is_visible=True).select_related("author")
        rating = request.query_params.get("rating", "")
        if rating:
            if rating not in {"1", "2", "3", "4", "5"}:
                raise serializers.ValidationError({"rating": "Choose a rating from 1 to 5."})
            reviews = reviews.filter(rating=int(rating))
        ordering = request.query_params.get("ordering", "newest")
        reviews = reviews.order_by({"highest": "-rating", "lowest": "rating"}.get(ordering, "-created_at"), "-id")
        paginator = ReviewPagination()
        page = paginator.paginate_queryset(reviews, request)
        response = paginator.get_paginated_response(ReviewSerializer(page, many=True).data)
        response.data["summary"] = review_summary(product)
        return response


class MyProductReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug, offering_slug):
        product = published_product(slug, offering_slug)
        review = product.reviews.filter(author=request.user).first()
        return Response({
            "can_review": has_purchase(request.user, product),
            "review": ReviewSerializer(review).data if review else None,
            "is_visible": review.is_visible if review else None,
        }, headers={"Cache-Control": "private, no-store"})

    def put(self, request, slug, offering_slug):
        product = published_product(slug, offering_slug)
        if not has_purchase(request.user, product):
            return Response({"error": {
                "code": "PURCHASE_REQUIRED",
                "message": "A paid purchase of this product linked to your account is required to write a review.",
                "details": {},
            }}, status=403)
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            # Serialize concurrent submissions for this product. A unique
            # constraint additionally enforces one review per author.
            Offering.objects.select_for_update().get(pk=product.pk)
            review, created = ProductReview.objects.update_or_create(
                offering=product,
                author=request.user,
                defaults={**serializer.validated_data, "verified_purchase": True},
            )
        return Response(ReviewSerializer(review).data, status=201 if created else 200)

    def delete(self, request, slug, offering_slug):
        product = published_product(slug, offering_slug)
        product.reviews.filter(author=request.user).delete()
        return Response(status=204)
