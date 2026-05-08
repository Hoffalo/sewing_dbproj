"""Role helpers mapped to Django Groups (see data migration)."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

User = get_user_model()

GROUP_OWNER = "Owner"
GROUP_MANAGER = "Manager"
GROUP_TAILOR = "Tailor"
GROUP_STAFF = "Staff"


def user_groups(user) -> set[str]:
    if not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def is_owner_or_manager(user) -> bool:
    return bool(
        user.is_superuser
        or user_groups(user) & {GROUP_OWNER, GROUP_MANAGER},
    )


def is_tailor(user) -> bool:
    return GROUP_TAILOR in user_groups(user)


def is_staff_role(user) -> bool:
    return GROUP_STAFF in user_groups(user)


def pick_actor_employee_id(user):
    """Resolve ``Employee`` PK for ``StatusHistory.changed_by`` / audit fields."""
    from apps.production.models import Employee

    if hasattr(user, "employee_profile"):
        return user.employee_profile.pk
    emp = Employee.objects.filter(active=True).first()
    if emp:
        return emp.pk
    raise PermissionDenied(_("No employee profile linked to this user."))
