"""DRF views — list/create/update for Customers + Orders, plus dashboard."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.db.models import Count, ProtectedError, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import Customer
from apps.orders.models import Currency, Material, Order
from apps.orders.status_flow import apply_crm_status
from apps.production.models import ProductionStage, Ticket

from .serializers import (
    CustomerSerializer,
    MaterialSerializer,
    OrderListSerializer,
    OrderSerializer,
    ProductionStageSerializer,
    TicketSerializer,
    to_float,
)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Customer.objects.annotate(order_count=Count("orders"))
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
            )
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Cannot delete this client — they still have orders. "
                        "Delete their orders first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.select_related("customer").prefetch_related(
            "items__measurements", "items__material_links__material"
        )
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """Reuse the canonical CRM transition rules (apps.orders.status_flow)."""
        order = self.get_object()
        target = request.data.get("status")
        if not target:
            return Response({"detail": "Missing 'status'."}, status=status.HTTP_400_BAD_REQUEST)
        ok, msg = apply_crm_status(order, target, request.user)
        if not ok:
            return Response({"detail": str(msg)}, status=status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        return Response(OrderListSerializer(order).data)


class ProductionStageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductionStage.objects.all().order_by("sequence")
    serializer_class = ProductionStageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.select_related("current_stage", "assigned_to__user")
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Material.objects.all().order_by("name")
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]


class DashboardView(APIView):
    """Aggregates for the Home page: status counts, weekly revenue, upcoming."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()

        # Counts by status (single GROUP BY).
        status_rows = (
            Order.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        # Always emit every choice, even with zero count.
        all_statuses = {choice: 0 for choice, _ in Order.Status.choices}
        for row in status_rows:
            all_statuses[row["status"]] = row["count"]
        orders_by_status = [
            {
                "status": code,
                "label": dict(Order.Status.choices)[code],
                "count": all_statuses[code],
            }
            for code, _ in Order.Status.choices
        ]

        # Weekly revenue per currency for the last 8 ISO weeks (delivered orders).
        eight_weeks_ago = today - timedelta(weeks=7)
        # Truncate to the Monday of `eight_weeks_ago`'s week.
        start = eight_weeks_ago - timedelta(days=eight_weeks_ago.weekday())
        delivered = Order.objects.filter(
            status=Order.Status.DELIVERED.value, order_date__gte=start
        ).values("currency", "order_date", "total_price")

        weekly: dict[str, dict[str, Decimal]] = {}
        for row in delivered:
            d = row["order_date"]
            week_start = d - timedelta(days=d.weekday())
            key = week_start.isoformat()
            weekly.setdefault(key, {})
            cur = row["currency"]
            weekly[key][cur] = weekly[key].get(cur, Decimal("0")) + (
                row["total_price"] or Decimal("0")
            )

        weekly_revenue = []
        # Emit one row per week in the window so the chart has a continuous x-axis.
        for i in range(8):
            week_start = start + timedelta(weeks=i)
            key = week_start.isoformat()
            entry = {"week_start": key}
            for cur, _ in Currency.choices:
                entry[cur] = to_float(weekly.get(key, {}).get(cur, Decimal("0")))
            weekly_revenue.append(entry)

        # This-week totals (per currency) for the stat card.
        this_week_start = today - timedelta(days=today.weekday())
        this_week = (
            Order.objects.filter(order_date__gte=this_week_start)
            .values("currency")
            .annotate(total=Sum("total_price"))
        )
        this_week_revenue = {row["currency"]: to_float(row["total"]) for row in this_week}

        # Upcoming non-terminal orders by due_date.
        upcoming_qs = (
            Order.objects.exclude(
                status__in=[Order.Status.DELIVERED.value, Order.Status.CANCELLED.value]
            )
            .select_related("customer")
            .order_by("due_date")[:10]
        )
        upcoming_orders = OrderListSerializer(upcoming_qs, many=True).data

        # Lightweight top-line stats.
        active_count = Order.objects.exclude(
            status__in=[Order.Status.DELIVERED.value, Order.Status.CANCELLED.value]
        ).count()
        overdue_count = Order.objects.filter(
            due_date__lt=today,
        ).exclude(
            status__in=[Order.Status.DELIVERED.value, Order.Status.CANCELLED.value]
        ).count()

        return Response(
            {
                "orders_by_status": orders_by_status,
                "weekly_revenue": weekly_revenue,
                "this_week_revenue": this_week_revenue,
                "upcoming_orders": upcoming_orders,
                "active_count": active_count,
                "overdue_count": overdue_count,
                "pending_count": all_statuses.get(Order.Status.PENDING.value, 0),
            }
        )


class TicketPDFView(APIView):
    """Serves the existing ReportLab PDF (apps.production.views.ticket_pdf)
    under the API namespace so the React app can link to it."""

    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_id: int):
        from apps.production.views import build_ticket_pdf  # lazy import — see views.py

        ticket = get_object_or_404(Ticket, pk=ticket_id)
        buf: BytesIO = build_ticket_pdf(ticket)
        return FileResponse(buf, as_attachment=True, filename=f"{ticket.code}.pdf")
