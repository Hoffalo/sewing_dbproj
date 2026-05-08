from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline, display

from apps.production.models import Delivery, Employee, ProductionStage, StatusHistory, Ticket
from sewing_shop.roles import is_owner_or_manager, is_staff_role, is_tailor, pick_actor_employee_id


class StatusHistoryInline(TabularInline):
    model = StatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ("stage", "changed_by", "changed_at", "comment", "allow_backward")
    ordering = ("-changed_at",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ("user", "role", "hired_on", "active")
    list_filter = ("role", "active", "hired_on")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    readonly_fields = ("user",)

    def has_delete_permission(self, request, obj=None):
        if not is_owner_or_manager(request.user):
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ProductionStage)
class ProductionStageAdmin(ModelAdmin):
    list_display = ("sequence", "name", "is_terminal")
    ordering = ("sequence",)

    def has_add_permission(self, request):
        return is_owner_or_manager(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_owner_or_manager(request.user)


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ("code", "order_item", "current_stage", "assigned_to", "priority", "deadline", "pdf_button")
    list_filter = ("current_stage", "priority", "assigned_to")
    search_fields = ("code", "order_item__description")
    autocomplete_fields = ("assigned_to",)
    readonly_fields = ("code", "print_ticket", "created_at", "updated_at")
    actions = ("advance_stage",)
    inlines = [StatusHistoryInline]

    fieldsets = (
        (_("Work ticket"), {"fields": ("code", "order_item", "print_ticket", "current_stage", "assigned_to", "priority", "deadline")}),
        (_("Audit"), {"fields": ("created_at", "updated_at")}),
    )

    def _pdf_link(self, obj):
        if not obj.pk:
            return ""
        url = reverse("production_ticket_pdf", args=[obj.pk])
        return format_html(
            '<a class="border border-base-200 rounded-md px-2 py-1 text-xs font-semibold '
            'hover:bg-base-100 dark:border-base-800" href="{}">{}</a>',
            url,
            _("Print ticket"),
        )

    @display(description=_("Print ticket"))
    def print_ticket(self, obj):
        return self._pdf_link(obj)

    @display(description=_("Print ticket"))
    def pdf_button(self, obj):
        return self._pdf_link(obj)

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if is_staff_role(request.user) and not is_owner_or_manager(request.user):
            return base + ["order_item", "current_stage", "assigned_to", "priority", "deadline"]
        return base

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "current_stage",
            "order_item__order__customer",
            "assigned_to__user",
        )
        if is_tailor(request.user) and not request.user.is_superuser:
            if hasattr(request.user, "employee_profile"):
                return qs.filter(assigned_to=request.user.employee_profile)
            return qs.none()
        return qs

    def has_change_permission(self, request, obj=None):
        if obj and is_tailor(request.user) and not request.user.is_superuser:
            if hasattr(request.user, "employee_profile") and obj.assigned_to_id == request.user.employee_profile.pk:
                return True
            return False
        if obj and is_staff_role(request.user) and not is_owner_or_manager(request.user):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if is_tailor(request.user) or is_staff_role(request.user):
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description=_("Advance stage / Avanzar etapa"))
    def advance_stage(self, request, queryset):
        if is_staff_role(request.user) and not request.user.is_superuser:
            raise PermissionDenied
        try:
            actor_id = pick_actor_employee_id(request.user)
        except PermissionDenied as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return
        moved = 0
        with transaction.atomic():
            for ticket in queryset.select_related("current_stage"):
                nxt = (
                    ProductionStage.objects.filter(sequence__gt=ticket.current_stage.sequence)
                    .order_by("sequence")
                    .first()
                )
                if nxt is None:
                    continue
                StatusHistory.objects.create(
                    ticket=ticket,
                    stage=nxt,
                    changed_by_id=actor_id,
                    comment=_("Advanced via admin action."),
                )
                moved += 1
        self.message_user(request, _("Updated %(n)s ticket(s).") % {"n": moved})


@admin.register(StatusHistory)
class StatusHistoryAdmin(ModelAdmin):
    list_display = ("ticket", "stage", "changed_by", "changed_at")
    list_filter = ("stage", "changed_at")
    search_fields = ("ticket__code", "comment")
    readonly_fields = ("ticket", "stage", "changed_by", "changed_at", "comment", "allow_backward")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return is_owner_or_manager(request.user)


@admin.register(Delivery)
class DeliveryAdmin(ModelAdmin):
    list_display = ("order", "delivered_at", "received_by", "delivered_by")
    list_filter = ("delivered_at",)
    search_fields = ("order__id", "received_by")
    autocomplete_fields = ("order", "delivered_by")

    def has_delete_permission(self, request, obj=None):
        if is_tailor(request.user) or is_staff_role(request.user):
            return False
        return super().has_delete_permission(request, obj)
