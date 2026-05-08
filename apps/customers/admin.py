from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.customers.models import Customer
from sewing_shop.roles import is_tailor


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("last_name", "first_name", "phone", "email", "created_at")
    list_display_links = ("last_name", "first_name")
    search_fields = ("first_name", "last_name", "phone", "email")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
    save_on_top = True
    fieldsets = (
        (_("Identity"), {"fields": ("first_name", "last_name", "phone", "email")}),
        (_("Address"), {"fields": ("address",)}),
        (_("Notes"), {"fields": ("notes",)}),
        (_("Audit"), {"fields": ("created_at", "updated_at")}),
    )

    def has_change_permission(self, request, obj=None):
        if is_tailor(request.user) and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
