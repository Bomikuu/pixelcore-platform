"""Live operational counts are all-time; sales series use business-local order dates."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.views import member_business
from .models import Order, ProductRequest


class LivePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


def local_today(business):
    return timezone.now().astimezone(ZoneInfo(business.timezone)).date()


def request_scopes(business):
    today, now = local_today(business), timezone.now()
    overdue = Q(kind='rental', status='collected', ends_on__lt=today)
    missed_pickup = Q(kind='rental', status='approved', starts_on__lt=today)
    return {
        'all': Q(), 'pending': Q(status='pending'),
        'held': Q(status='held', expires_at__gt=now),
        'rentals': Q(kind='rental', status__in=['approved', 'collected']),
        'overdue': overdue, 'due_today': Q(kind='rental', status='collected', ends_on=today),
        'missed_pickup': missed_pickup,
        'attention': overdue | missed_pickup | Q(status='pending'),
        'returned': Q(status='returned'),
        'closed': Q(status__in=['returned', 'converted', 'cancelled', 'rejected', 'expired']) | Q(status='held', expires_at__lte=now),
    }


def request_counts(business):
    return ProductRequest.objects.filter(business=business).aggregate(**{
        key: Count('id', filter=value) for key, value in request_scopes(business).items()
    })


ORDER_SCOPES = {
    'all': Q(), 'active': Q(status__in=['pending', 'confirmed', 'processing']),
    'unpaid': Q(payment_status__in=['unpaid', 'pending']) & ~Q(status__in=['cancelled', 'refunded']),
    'delivery': Q(fulfillment_type='delivery', status__in=['pending', 'confirmed', 'processing']),
    'fulfilled': Q(status='fulfilled'), 'cancelled': Q(status='cancelled'),
    'refunded': Q(payment_status__in=['refunded', 'partially_refunded']),
}


def order_counts(business):
    return Order.objects.filter(business=business).aggregate(**{
        key: Count('id', filter=value) for key, value in ORDER_SCOPES.items()
    })


class LiveSalesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, business_public_id):
        business = member_business(request.user, business_public_id)
        field = serializers.ChoiceField(choices=['7', '30', '90'])
        days = int(field.run_validation(request.query_params.get('days', '30')))
        zone, today = ZoneInfo(business.timezone), local_today(business)
        start = today - timedelta(days=days - 1)
        orders = Order.objects.filter(business=business)
        period = orders.filter(placed_at__gte=datetime.combine(start, time.min, tzinfo=zone), placed_at__lt=datetime.combine(today + timedelta(days=1), time.min, tzinfo=zone))
        # Value of orders currently fully paid, grouped by placement date, not cash receipts.
        paid = period.filter(payment_status='paid').exclude(status__in=['cancelled', 'refunded'])
        series = {row['day']: row['value'] for row in paid.annotate(day=TruncDate('placed_at', tzinfo=zone)).values('day').annotate(value=Sum('grand_total')).order_by('day')}
        totals = paid.aggregate(value=Sum('grand_total'), count=Count('id'))
        can_manage = business.memberships.filter(user=request.user, status='active', role__in=['owner', 'admin', 'manager']).exists()
        return Response({
            'as_of': timezone.now(), 'timezone': business.timezone, 'currency': business.currency,
            'date_from': start, 'date_to': today, 'days': days, 'can_manage_requests': can_manage,
            'sales': {'paid_order_value': str(totals['value'] or Decimal('0')), 'paid_orders': totals['count'],
                      'orders_placed': period.count(), 'average_paid_order': str((totals['value'] / totals['count']).quantize(Decimal('.01')) if totals['count'] else '0')},
            'series': [{'date': start + timedelta(days=index), 'value': str(series.get(start + timedelta(days=index), 0))} for index in range(days)],
            'orders': order_counts(business), 'requests': request_counts(business) if can_manage else None,
        })
