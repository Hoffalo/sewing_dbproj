"""
Order domain models (pedidos, garments, materials, M2M through-table).

Deliberate denormalization documented on ``Order.total_price``.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from apps.customers.models import Customer


class Order(models.Model):
    """Customer order header.

    **Denormalized aggregate: ``total_price``**

    Storing ``total_price`` duplicates information derivable from line items
    (Σ quantity × unit_price). We keep it **read-optimized** for frequent admin
    list filtering/sorting while **writing** the value from signals whenever
    ``OrderItem`` rows change, preserving consistency without violating 3NF’s
    intent for operational data — the canonical facts remain the line items.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        IN_PRODUCTION = "IN_PRODUCTION", _("In production")
        READY = "READY", _("Ready")
        DELIVERED = "DELIVERED", _("Delivered")
        CANCELLED = "CANCELLED", _("Cancelled")

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
        db_index=True,
        verbose_name=_("Customer"),
    )
    order_date = models.DateField(
        default=date.today,
        db_index=True,
        verbose_name=_("Order date"),
    )
    due_date = models.DateField(db_index=True, verbose_name=_("Due date"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Total price"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-order_date", "-id"]
        constraints = [
            models.CheckConstraint(
                check=Q(due_date__gte=F("order_date")),
                name="order_due_on_or_after_order_date",
            ),
        ]

    def __str__(self) -> str:
        if self.pk:
            return f"#{self.pk} — {self.customer}"
        return str(_("(unsaved order)"))


class OrderItem(models.Model):
    """Line item (garment) belonging to an order."""

    class GarmentType(models.TextChoices):
        DRESS = "DRESS", _("Dress")
        SUIT = "SUIT", _("Suit")
        SHIRT = "SHIRT", _("Shirt")
        PANTS = "PANTS", _("Pants")
        SKIRT = "SKIRT", _("Skirt")
        ALTERATION = "ALTERATION", _("Alteration")
        OTHER = "OTHER", _("Other")

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        db_index=True,
        verbose_name=_("Order"),
    )
    garment_type = models.CharField(
        max_length=20,
        choices=GarmentType.choices,
        verbose_name=_("Garment type"),
    )
    description = models.TextField(verbose_name=_("Description"))
    fabric = models.CharField(max_length=120, blank=True, verbose_name=_("Fabric"))
    color = models.CharField(max_length=120, blank=True, verbose_name=_("Color"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Unit price"),
    )
    design_notes = models.TextField(blank=True, verbose_name=_("Design notes"))
    position = models.PositiveIntegerField(verbose_name=_("Position"))

    class Meta:
        verbose_name = _("Order line")
        verbose_name_plural = _("Order lines")
        ordering = ["order", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "position"],
                name="unique_order_line_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_garment_type_display()} — {self.description[:40]}"


class Measurement(models.Model):
    """Measurements per order line (atomic name/value pairs — no repeating groups)."""

    class Name(models.TextChoices):
        BUST = "BUST", _("Bust")
        WAIST = "WAIST", _("Waist")
        HIPS = "HIPS", _("Hips")
        INSEAM = "INSEAM", _("Inseam")
        SLEEVE = "SLEEVE", _("Sleeve")
        SHOULDER = "SHOULDER", _("Shoulder")
        NECK = "NECK", _("Neck")
        LENGTH = "LENGTH", _("Length")
        OTHER = "OTHER", _("Other")

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="measurements",
        db_index=True,
        verbose_name=_("Order line"),
    )
    name = models.CharField(max_length=20, choices=Name.choices, verbose_name=_("Measurement"))
    value_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Value (cm)"),
    )
    notes = models.CharField(max_length=255, blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Measurement")
        verbose_name_plural = _("Measurements")
        constraints = [
            models.UniqueConstraint(
                fields=["order_item", "name"],
                name="unique_measurement_per_line_and_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_name_display()}: {self.value_cm} cm"


class Material(models.Model):
    """Inventory reference (catalog + stock)."""

    class Unit(models.TextChoices):
        METER = "METER", _("Meter")
        UNIT = "UNIT", _("Unit")
        GRAM = "GRAM", _("Gram")
        SPOOL = "SPOOL", _("Spool")

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))
    unit = models.CharField(max_length=10, choices=Unit.choices, verbose_name=_("Unit"))
    stock_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Stock quantity"),
    )
    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Cost per unit"),
    )

    class Meta:
        verbose_name = _("Material")
        verbose_name_plural = _("Materials")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class OrderItemMaterial(models.Model):
    """
    Explicit M2M with attributes (3NF).

    Avoids a repeating group on ``OrderItem`` (material IDs + quantities as
    parallel arrays) by decomposing into a separate relation with its own key.
    """

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="material_links",
        db_index=True,
        verbose_name=_("Order line"),
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="order_links",
        db_index=True,
        verbose_name=_("Material"),
    )
    quantity_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Quantity used"),
    )

    class Meta:
        verbose_name = _("Line material")
        verbose_name_plural = _("Line materials")
        constraints = [
            models.UniqueConstraint(
                fields=["order_item", "material"],
                name="unique_material_per_order_line",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order_item_id}: {self.material} ({self.quantity_used})"
