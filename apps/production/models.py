"""
Production domain: employees, tickets (work orders), stages, audit trail, delivery.

``ProductionStage`` is a reference table (not a Python ``TextChoices`` enum) so
the owner can add/rename/resequence stages without schema migrations.

``Ticket.current_stage`` is documented as a deliberate denormalization for
read-heavy admin queries; signals sync it from ``StatusHistory``.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order, OrderItem


class Employee(models.Model):
    """Shop staff linked to Django auth."""

    class Role(models.TextChoices):
        OWNER = "OWNER", _("Owner")
        MANAGER = "MANAGER", _("Manager")
        TAILOR = "TAILOR", _("Tailor")
        STAFF = "STAFF", _("Staff")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
        db_index=True,
        verbose_name=_("User"),
    )
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name=_("Role"))
    hired_on = models.DateField(verbose_name=_("Hired on"))
    active = models.BooleanField(default=True, db_index=True, verbose_name=_("Active"))

    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")

    def __str__(self) -> str:
        return f"{self.user.get_username()} ({self.get_role_display()})"


class ProductionStage(models.Model):
    """
    Canonical pipeline step.

    Modeled as a table rather than ``choices`` because (a) the owner may add
    stages, (b) ``sequence`` supports validating forward-only progression in
    ``StatusHistory``, and (c) it normalizes the one-to-many relationship from
    stage definitions to ``StatusHistory`` rows.
    """

    name = models.CharField(max_length=64, unique=True, verbose_name=_("Name"))
    sequence = models.PositiveIntegerField(unique=True, verbose_name=_("Sequence"))
    is_terminal = models.BooleanField(default=False, db_index=True, verbose_name=_("Is terminal"))

    class Meta:
        verbose_name = _("Production stage")
        verbose_name_plural = _("Production stages")
        ordering = ["sequence"]

    def __str__(self) -> str:
        return self.name


class Ticket(models.Model):
    """Work order for a single garment line."""

    class Priority(models.IntegerChoices):
        LOW = 1, _("Low")
        NORMAL = 2, _("Normal")
        HIGH = 3, _("High")
        URGENT = 4, _("Urgent")

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="tickets",
        db_index=True,
        verbose_name=_("Order line"),
    )
    code = models.CharField(max_length=32, unique=True, verbose_name=_("Code"))
    current_stage = models.ForeignKey(
        ProductionStage,
        on_delete=models.PROTECT,
        related_name="tickets_at_stage",
        db_index=True,
        verbose_name=_("Current stage"),
        help_text=_(
            "Denormalized from latest StatusHistory for fast filtering; kept in sync via signals."
        ),
    )
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        db_index=True,
        verbose_name=_("Assigned to"),
    )
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_index=True,
        verbose_name=_("Priority"),
    )
    deadline = models.DateField(null=True, blank=True, db_index=True, verbose_name=_("Deadline"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self) -> str:
        from django.utils import timezone

        year = timezone.now().year
        prefix = f"TCK-{year}-"
        siblings = Ticket.objects.filter(code__startswith=prefix).values_list("code", flat=True)
        max_n = 0
        for code in siblings:
            try:
                n = int(code.split("-")[-1])
                max_n = max(max_n, n)
            except (ValueError, IndexError):
                continue
        return f"{prefix}{max_n + 1:04d}"


class StatusHistory(models.Model):
    """Append-only stage transitions for auditability."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="history",
        db_index=True,
        verbose_name=_("Ticket"),
    )
    stage = models.ForeignKey(
        ProductionStage,
        on_delete=models.PROTECT,
        related_name="status_events",
        db_index=True,
        verbose_name=_("Stage"),
    )
    changed_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="status_changes",
        db_index=True,
        verbose_name=_("Changed by"),
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Changed at"))
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    allow_backward = models.BooleanField(
        default=False,
        verbose_name=_("Allow backward move"),
        help_text=_("Supervisor override to move to an earlier sequence."),
    )

    class Meta:
        verbose_name = _("Status history")
        verbose_name_plural = _("Status history")
        ordering = ["-changed_at"]

    def __str__(self) -> str:
        return f"{self.ticket.code} → {self.stage.name}"

    def clean(self):
        from django.db.models import Max

        if self.pk:
            return
        max_seq = (
            StatusHistory.objects.filter(ticket=self.ticket).aggregate(Max("stage__sequence"))[
                "stage__sequence__max"
            ]
        )
        if max_seq is not None and self.stage.sequence < max_seq and not self.allow_backward:
            raise ValidationError(
                _("Stage sequence may not go backwards without the override flag.")
            )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError(_("Status history is append-only and cannot be updated."))
        self.full_clean()
        super().save(*args, **kwargs)


class Delivery(models.Model):
    """Proof of pickup — one per completed order."""

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="delivery",
        db_index=True,
        verbose_name=_("Order"),
    )
    delivered_at = models.DateTimeField(db_index=True, verbose_name=_("Delivered at"))
    received_by = models.CharField(max_length=255, verbose_name=_("Received by"))
    delivered_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="deliveries",
        db_index=True,
        verbose_name=_("Delivered by"),
    )
    final_observations = models.TextField(blank=True, verbose_name=_("Final observations"))

    class Meta:
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")

    def __str__(self) -> str:
        return f"{self.order_id} @ {self.delivered_at.isoformat(timespec='minutes')}"
