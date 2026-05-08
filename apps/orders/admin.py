from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline, display

from apps.orders.models import Material, Order, OrderItem, OrderItemMaterial, Measurement
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
    inlines = [MeasurementInline, OrderItemMaterialInline]


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
    list_display = ("name", "unit", "stock_quantity", "cost_per_unit")
    search_fields = ("name",)
    list_filter = ("unit",)

    def has_change_permission(self, request, obj=None):
        if is_tailor(request.user) and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id",
        "customer",
        "order_date",
        "due_date",
        "status_badge",
        "total_price",
    )
    list_filter = ("status", "order_date", "due_date")
    search_fields = ("customer__first_name", "customer__last_name", "customer__phone", "notes")
    autocomplete_fields = ("customer",)
    readonly_fields = ("total_price", "created_at", "updated_at")
    inlines = [OrderItemInline]
    actions = ("generate_tickets", "mark_delivered")

    fieldsets = (
        (_("Order"), {"fields": ("customer", "order_date", "due_date", "status", "total_price")}),
        (_("Notes"), {"fields": ("notes",)}),
        (_("Audit"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<span class="rounded-full bg-primary-600/10 px-2 py-0.5 text-xs font-semibold text-primary-800 '
            'dark:text-primary-100">{}</span>',
            obj.get_status_display(),
        )

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == Order.Status.DELIVERED:
            return base + ["customer", "order_date", "due_date", "status", "notes"]
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
                "<path:object_id>/deliver/",
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


