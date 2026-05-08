"""Order lifecycle — pipeline moves, CRM board, DELIVERED only via Delivery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.orders.models import Order
from sewing_shop.roles import is_owner_or_manager

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

ORDER_PIPELINE = (
    Order.Status.PENDING.value,
    Order.Status.IN_PRODUCTION.value,
    Order.Status.READY.value,
)


def pipeline_index(status: str) -> int | None:
    try:
        return ORDER_PIPELINE.index(status)
    except ValueError:
        return None


def get_next_pipeline_status(order: Order) -> str | None:
    idx = pipeline_index(order.status)
    if idx is None or idx >= len(ORDER_PIPELINE) - 1:
        return None
    return ORDER_PIPELINE[idx + 1]


def validate_crm_transition(order: Order, target: str, user) -> tuple[bool, str | None]:
    from django.contrib.auth.models import AnonymousUser
    from django.utils.translation import gettext_lazy as _

    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False, _("Authentication required.")

    if target == order.status:
        return True, None

    # Reverting a delivered order is a correction — require Owner/Manager.
    if order.status == Order.Status.DELIVERED.value:
        if not is_owner_or_manager(user):
            return False, _("Only owner or manager can change a delivered order.")
        return True, None

    # Marking complete from any non-delivered state — open to all roles.
    if target == Order.Status.DELIVERED.value:
        return True, None

    if target == Order.Status.CANCELLED.value:
        if not is_owner_or_manager(user):
            return False, _("Only owner or manager can cancel.")
        return True, None

    # Otherwise the move must stay inside the regular pipeline.
    if target not in ORDER_PIPELINE or order.status not in ORDER_PIPELINE:
        # Off-pipeline source (e.g. CANCELLED) can be reopened by Owner/Manager.
        if not is_owner_or_manager(user):
            return False, _("Invalid CRM move.")
        return True, None

    old_i = pipeline_index(order.status)
    new_i = pipeline_index(target)
    assert old_i is not None and new_i is not None

    if new_i < old_i and not is_owner_or_manager(user):
        return False, _("Only owner or manager can move an order backward in the pipeline.")

    return True, None


def advance_one_pipeline_step(order: Order, user) -> tuple[bool, str | None]:
    from django.utils.translation import gettext_lazy as _

    nxt = get_next_pipeline_status(order)
    if not nxt:
        return False, _("Already at last pipeline step — deliver or cancel if needed.")

    ok, msg = validate_crm_transition(order, nxt, user)
    if not ok:
        return False, msg
    order.status = nxt  # type: ignore[assignment]
    order.save(update_fields=["status", "updated_at"])
    return True, None


def apply_crm_status(order: Order, target: str, user) -> tuple[bool, str | None]:
    ok, msg = validate_crm_transition(order, target, user)
    if not ok:
        return False, msg
    order.status = target  # type: ignore[assignment]
    order.save(update_fields=["status", "updated_at"])
    return True, None
