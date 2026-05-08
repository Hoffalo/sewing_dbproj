from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import display
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from apps.orders.money import format_money
from apps.orders.models import Currency, Material, Measurement, Order, OrderItem, OrderItemMaterial
from apps.orders.status_flow import (
    ORDER_PIPELINE,
    advance_one_pipeline_step,
    apply_crm_status,
    get_next_pipeline_status,
)
from apps.production.models import Delivery, Employee, ProductionStage, StatusHistory, Ticket
from sewing_shop.roles import (
    is_owner_or_manager,
    is_staff_role,
    is_tailor,
    pick_actor_employee_id,
)


class MeasurementInline(TabularInline):
    model = Measurement
    extra = 0


class OrderItemMaterialInline(TabularInline):
    model = OrderItemMaterial
    extra = 0
    autocomplete_fields = ("material",)


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    show_change_link = True
    readonly_fields = ("formatted_unit_price_display", "line_total_display")
    fields = (
        "position",
        "garment_type",
        "description",
        "fabric",
        "color",
        "quantity",
        "unit_price",
        "formatted_unit_price_display",
        "line_total_display",
        "design_notes",
    )
    inlines = [MeasurementInline, OrderItemMaterialInline]

    @display(description=_("Unit price"))
    def formatted_unit_price_display(self, obj):
        if not obj.pk or not getattr(obj, "order_id", None):
            return "—"
        return format_money(obj.unit_price, obj.order.currency)

    @display(description=_("Line total"))
    def line_total_display(self, obj):
        if not obj.pk or not getattr(obj, "order_id", None):
            return "—"
        total = Decimal(obj.quantity) * obj.unit_price
        return format_money(total, obj.order.currency)


class DeliveryForm(forms.Form):
    received_by = forms.CharField(label=_("Received by"))
    delivered_by = forms.ModelChoiceField(
        queryset=Employee.objects.filter(active=True).select_related("user"),
        label=_("Delivered by"),
    )
    final_observations = forms.CharField(
        label=_("Final observations"),
        widget=forms.Textarea,
        required=False,
    )


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ("name", "unit", "currency_badge", "formatted_cost", "stock_quantity")
    search_fields = ("name",)
    list_filter = ("unit", "currency")
    list_display_links = ("name",)
    save_on_top = True

    @display(description=_("Currency"))
    def currency_badge(self, obj):
        return _currency_markup(obj.currency, obj.get_currency_display())

    @display(description=_("Cost per unit"), ordering="cost_per_unit")
    def formatted_cost(self, obj):
        return format_money(obj.cost_per_unit, obj.currency)

    def has_change_permission(self, request, obj=None):
        if is_tailor(request.user) and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)


def _currency_markup(code: str, label: str) -> str:
    css = {
        Currency.EUR: "bg-green-600/15 text-green-900 ring-1 ring-green-700/25 dark:bg-green-500/15 dark:text-green-100 dark:ring-green-400/35",
        Currency.COP: "bg-amber-500/15 text-amber-950 ring-1 ring-amber-600/35 dark:bg-amber-400/15 dark:text-amber-50 dark:ring-amber-400/30",
        Currency.USD: "bg-blue-600/15 text-blue-950 ring-1 ring-blue-700/25 dark:bg-blue-500/15 dark:text-blue-100 dark:ring-blue-400/35",
    }.get(
        code,
        "bg-base-100 text-font-default-light ring-1 ring-base-300 dark:bg-base-900 dark:text-font-default-dark",
    )
    return format_html(
        '<span class="inline-flex whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold {}">{}</span>',
        css,
        label,
    )


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id",
        "customer",
        "order_date",
        "due_date",
        "status_badge",
        "advance_quick",
        "currency_badge",
        "formatted_total",
    )
    list_display_links = ("id", "customer")
    save_on_top = True
    list_filter = ("status", "currency", "order_date", "due_date")
    search_fields = ("customer__first_name", "customer__last_name", "customer__phone", "notes")
    autocomplete_fields = ("customer",)
    date_hierarchy = "order_date"
    readonly_fields = ("total_price", "created_at", "updated_at")
    inlines = [OrderItemInline]
    actions = ("generate_tickets", "mark_delivered")

    class Media:
        js = ("orders/order_advance.js",)

    fieldsets = (
        (_("Order"), {"fields": ("customer", "order_date", "due_date", "status")}),
        (_("Pricing"), {"fields": ("currency", "total_price")}),
        (_("Notes"), {"fields": ("notes",)}),
        (_("Audit"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Next step"))
    def advance_quick(self, obj):
        if not obj.pk:
            return "—"
        if obj.status in (Order.Status.DELIVERED.value, Order.Status.CANCELLED.value):
            return "—"
        if get_next_pipeline_status(obj) is None:
            return format_html(
                '<span class="text-xs text-font-subtle-light dark:text-font-subtle-dark">—</span>',
            )
        url = reverse("admin:orders_order_advance", args=[obj.pk])
        return format_html(
            '<button type="button" class="js-order-advance inline-flex rounded-lg bg-primary-600 px-2.5 py-1 '
            'text-xs font-semibold text-white shadow-sm ring-1 ring-primary-700/20 transition '
            'hover:bg-primary-500 active:translate-y-[0.5px] dark:ring-white/15" '
            'data-advance-url="{}">{}</button>',
            url,
            _("Next"),
        )

    @display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<span class="rounded-full bg-primary-600/10 px-2 py-0.5 text-xs font-semibold text-primary-800 '
            'dark:text-primary-100">{}</span>',
            obj.get_status_display(),
        )

    @display(description=_("Currency"), ordering="currency")
    def currency_badge(self, obj):
        return _currency_markup(obj.currency, obj.get_currency_display())

    @display(description=_("Total"), ordering="total_price")
    def formatted_total(self, obj):
        return format_money(obj.total_price, obj.currency)

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == Order.Status.DELIVERED.value:
            return base + ["customer", "order_date", "due_date", "status", "currency", "notes"]
        return base

    def has_delete_permission(self, request, obj=None):
        if is_tailor(request.user) or is_staff_role(request.user):
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if is_tailor(request.user) and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def get_urls(self):
        return [
            path(
                "crm-board/",
                self.admin_site.admin_view(self.order_crm_board),
                name="orders_order_crm_board",
            ),
            path(
                "crm-move/",
                self.admin_site.admin_view(self.order_crm_move_view),
                name="orders_order_crm_move",
            ),
            path(
                "<int:object_id>/advance/",
                self.admin_site.admin_view(self.advance_order_ajax),
                name="orders_order_advance",
            ),
            path(
                "<int:object_id>/deliver/",
                self.admin_site.admin_view(self.mark_delivered_view),
                name="orders_order_deliver",
            ),
        ] + super().get_urls()

    @admin.action(description=_("Generate tickets (RECEIVED) for selected orders"))
    def generate_tickets(self, request, queryset):
        if not is_owner_or_manager(request.user):
            raise PermissionDenied
        stage = ProductionStage.objects.filter(name="RECEIVED").first()
        if not stage:
            self.message_user(request, _("Missing RECEIVED stage — run migrations."), level=messages.ERROR)
            return
        created = 0
        try:
            actor_id = pick_actor_employee_id(request.user)
        except PermissionDenied as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return
        with transaction.atomic():
            for order in queryset:
                for item in order.items.all():
                    if item.tickets.exists():
                        continue
                    ticket = Ticket(order_item=item, current_stage=stage, code="")
                    ticket.save()
                    StatusHistory.objects.create(
                        ticket=ticket,
                        stage=stage,
                        changed_by_id=actor_id,
                        comment=_("Ticket opened from admin."),
                    )
                    created += 1
        self.message_user(request, _("Created %(n)s ticket(s).") % {"n": created})

    @admin.action(description=_("Mark as delivered…"))
    def mark_delivered(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _("Select exactly one order."), level=messages.ERROR)
            return
        order = queryset.first()
        return HttpResponseRedirect(reverse("admin:orders_order_deliver", args=[order.pk]))

    def mark_delivered_view(self, request, object_id):
        order = get_object_or_404(Order.objects.select_related("customer"), pk=object_id)
        if not self.has_change_permission(request, order):
            raise PermissionDenied
        if not is_owner_or_manager(request.user):
            raise PermissionDenied
        if hasattr(order, "delivery"):
            self.message_user(request, _("This order already has a delivery record."), level=messages.WARNING)
            return HttpResponseRedirect(reverse("admin:orders_order_change", args=[order.pk]))
        if request.method == "POST":
            form = DeliveryForm(request.POST)
            if form.is_valid():
                Delivery.objects.create(
                    order=order,
                    delivered_by=form.cleaned_data["delivered_by"],
                    received_by=form.cleaned_data["received_by"],
                    final_observations=form.cleaned_data.get("final_observations") or "",
                    delivered_at=timezone.now(),
                )
                self.message_user(request, _("Delivery recorded."))
                return HttpResponseRedirect(reverse("admin:orders_order_change", args=[order.pk]))
        else:
            form = DeliveryForm()
        context = {
            **self.admin_site.each_context(request),
            "title": _("Record delivery"),
            "opts": self.model._meta,
            "order": order,
            "form": form,
        }
        return render(request, "admin/orders/deliver_intermediate.html", context)

    def order_crm_board(self, request):
        from collections import defaultdict

        if not self.has_view_permission(request):
            raise PermissionDenied
        qs = (
            Order.objects.exclude(status=Order.Status.DELIVERED)
            .select_related("customer")
            .order_by("-order_date", "-pk")
        )
        buckets = defaultdict(list)
        for o in qs:
            buckets[o.status].append(o)
        columns = [
            {
                "status": code,
                "label": str(Order.Status(code).label),
                "orders": buckets.get(code, []),
            }
            for code in ORDER_PIPELINE
        ]
        columns.append(
            {
                "status": Order.Status.CANCELLED.value,
                "label": str(Order.Status.CANCELLED.label),
                "orders": buckets.get(Order.Status.CANCELLED.value, []),
            },
        )
        for col in columns:
            for o in col["orders"]:
                o.str_money = format_money(o.total_price, o.currency)
        context = {
            **self.admin_site.each_context(request),
            "title": _("Order CRM board"),
            "opts": self.model._meta,
            "columns": columns,
            "move_url": reverse("admin:orders_order_crm_move"),
        }
        return render(request, "admin/orders/crm_board.html", context)

    @method_decorator(require_POST)
    def order_crm_move_view(self, request):
        import json

        if not self.has_change_permission(request):
            return JsonResponse({"error": str(_("No permission."))}, status=403)
        try:
            data = json.loads(request.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": str(_("Invalid JSON."))}, status=400)
        oid = data.get("order_id")
        tgt = data.get("to_status")
        order = get_object_or_404(Order.objects.select_related("customer"), pk=oid)
        if not self.has_change_permission(request, order):
            return JsonResponse({"error": str(_("No permission."))}, status=403)
        ok, msg = apply_crm_status(order, str(tgt), request.user)
        if not ok:
            return JsonResponse({"error": str(msg)}, status=400)
        return JsonResponse({"ok": True})

    @method_decorator(require_POST)
    def advance_order_ajax(self, request, object_id):
        order = get_object_or_404(Order, pk=object_id)
        if not self.has_change_permission(request, order):
            return JsonResponse({"error": str(_("No permission."))}, status=403)
        ok, msg = advance_one_pipeline_step(order, request.user)
        if not ok:
            return JsonResponse({"error": str(msg)}, status=400)
        return JsonResponse({"ok": True})


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    """
    Exists so Ticket (and related) FK autocomplete has a searchable admin target.
    """

    list_display = ("id", "order", "garment_type", "description")
    list_display_links = ("id",)
    search_fields = (
        "description",
        "order__pk",
        "order__customer__first_name",
        "order__customer__last_name",
        "order__customer__phone",
    )
    autocomplete_fields = ("order",)


