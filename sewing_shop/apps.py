from django.apps import AppConfig


class SewingShopConfig(AppConfig):
    """Project package so local management commands (e.g. ``seed_demo``) are discovered."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "sewing_shop"
    verbose_name = "Sewing shop project"
