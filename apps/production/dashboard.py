"""
Operational metrics for Unfold ``DASHBOARD_CALLBACK`` — KPIs, per-currency revenue, stages chart.
"""

from django.db.models import Count, Sum
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.orders.money import format_money
from apps.orders.models import Currency, Order
from apps.production.models import Ticket


def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    today = timezone.localdate()
    month_start_dt = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    orders_changelist = reverse("admin:orders_order_changelist")

    delivered_qs = Order.objects.filter(
        status=Order.Status.DELIVERED,
        updated_at__gte=month_start_dt,
    )

    context["kpi_cards"] = [
        {
            "title": _("Pending"),
            "value": Order.objects.filter(status=Order.Status.PENDING).count(),
            "url": f"{orders_changelist}?status__exact={Order.Status.PENDING}",
            "icon": "schedule",
            "color": "amber",
        },
        {
            "title": _("In production"),
            "value": Order.objects.filter(status=Order.Status.IN_PRODUCTION).count(),
            "url": f"{orders_changelist}?status__exact={Order.Status.IN_PRODUCTION}",
            "icon": "build",
            "color": "blue",
        },
        {
            "title": _("Overdue"),
            "value": Order.objects.filter(due_date__lt=today)
            .exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
            .count(),
            "url": orders_changelist,
            "icon": "warning",
            "color": "red",
        },
        {
            "title": _("Delivered this month"),
            "value": delivered_qs.count(),
            "url": f"{orders_changelist}?status__exact={Order.Status.DELIVERED}",
            "icon": "check_circle",
            "color": "green",
        },
    ]

    revenue_cards = []
    for code, label in Currency.choices:
        total = (
            Order.objects.filter(
                status=Order.Status.DELIVERED,
                updated_at__gte=month_start_dt,
                currency=code,
            ).aggregate(s=Sum("total_price"))["s"]
        )
        if total:
            revenue_cards.append(
                {
                    "currency": code,
                    "label": str(label),
                    "amount": format_money(total, code),
                }
            )
    context["revenue_cards"] = revenue_cards

    stage_rows = list(
        Ticket.objects.values("current_stage__name", "current_stage__sequence")
        .annotate(count=Count("id"))
        .order_by("current_stage__sequence")
    )
    context["stage_chart"] = {
        "labels": [r["current_stage__name"] or "—" for r in stage_rows],
        "data": [r["count"] for r in stage_rows],
    }

    overdue_qs = (
        Order.objects.filter(due_date__lt=today)
        .exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
        .select_related("customer")
        .order_by("due_date")[:5]
    )
    context["overdue_orders"] = [
        {
            "order": o,
            "formatted_total": format_money(o.total_price, o.currency),
        }
        for o in overdue_qs
    ]

    return context
