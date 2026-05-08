"""
Customer model — third normal form.

Stores only facts about the customer; orders reference this table by FK (no
name/phone duplication on pedidos) to eliminate transitive dependencies.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    first_name = models.CharField(
        max_length=120,
        verbose_name=_("First name"),
    )
    last_name = models.CharField(
        max_length=120,
        verbose_name=_("Last name"),
    )
    phone = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        verbose_name=_("Phone"),
        help_text=_("Primary contact key for walk-in clients."),
    )
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    address = models.TextField(blank=True, verbose_name=_("Address"))
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Preferences, fabric allergies, etc."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.phone})"
