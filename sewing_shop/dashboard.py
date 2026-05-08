"""
Admin index dashboard metrics for Costuras Lucía (Unfold ``DASHBOARD_CALLBACK``).
"""

from datetime import timedelta

from django.db.models import Count
from django.http import HttpRequest
from django.utils import timezone

from apps.orders.models import Order
from apps.production.models import Delivery, Ticket


def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    today = timezone.localdate()
    month_start = today.replace(day=1)
    since_30 = timezone.now() - timedelta(days=30)

    pending = Order.objects.filter(status=Order.Status.PENDING).count()
    in_prod = Order.objects.filter(status=Order.Status.IN_PRODUCTION).count()
    overdue = Order.objects.filter(
        due_date__lt=today,
    ).exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED]).count()
    delivered_m = Delivery.objects.filter(delivered_at__date__gte=month_start).count()

    orders_by_status = list(
        Order.objects.filter(order_date__gte=since_30.date())
        .values("status")
        .annotate(c=Count("id"))
        .order_by()
    )
    status_labels = {k: v for k, v in Order.Status.choices}
    order_chart = {
        "labels": [str(status_labels.get(r["status"], r["status"])) for r in orders_by_status],
        "data": [r["c"] for r in orders_by_status],
    }

    tickets_by_stage = list(
        Ticket.objects.values(
            "current_stage__name",
            "current_stage__sequence",
        )
        .annotate(c=Count("id"))
        .order_by("current_stage__sequence")
    )
    tickets_chart = {
        "labels": [r["current_stage__name"] or "—" for r in tickets_by_stage],
        "data": [r["c"] for r in tickets_by_stage],
    }

    overdue_rows = list(
        Order.objects.filter(due_date__lt=today)
        .exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
        .select_related("customer")
        .order_by("due_date")[:5]
    )

    context.update(
        {
            "dashboard_metrics": {
                "pending": pending,
                "in_production": in_prod,
                "overdue": overdue,
                "delivered_month": delivered_m,
            },
            "dashboard_order_chart": order_chart,
            "dashboard_tickets_chart": tickets_chart,
            "dashboard_overdue": overdue_rows,
        }
    )
    return context
