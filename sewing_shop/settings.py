"""
Django settings for Costuras Lucía — sewing shop management (course project).
Spanish-first UI with English toggle; PostgreSQL + Django Unfold admin.
"""

from pathlib import Path
import os

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-default-do-not-use")

DEBUG = os.environ.get("DEBUG", "0") == "1"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

INSTALLED_APPS = [
    "sewing_shop.apps.SewingShopConfig",
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "apps.customers.apps.CustomersConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.production.apps.ProductionConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sewing_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "sewing_shop.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "sewing_shop"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        # Default to localhost for `manage.py` on your machine; Docker Compose sets POSTGRES_HOST=db for `web`.
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"

TIME_ZONE = "America/Bogota"

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ("es", _("Spanish")),
    ("en", _("English")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


def _sidebar_link(model_route: str, label: str):
    """Build admin changelist link (e.g. model_route='customers_customer')."""
    return {
        "title": _(label),
        "icon": "inventory",
        "link": reverse_lazy(f"admin:{model_route}_changelist"),
    }


UNFOLD = {
    "SITE_TITLE": "Costuras Lucía",
    "SITE_HEADER": _("Costuras Lucía"),
    "SITE_SUBHEADER": _("Sewing shop management"),
    "SITE_SYMBOL": "styler",
    "SHOW_LANGUAGES": True,
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": _("Clients"),
                "separator": True,
                "items": [
                    _sidebar_link("customers_customer", _("Customers")),
                ],
            },
            {
                "title": _("Orders"),
                "separator": True,
                "items": [
                    _sidebar_link("orders_order", _("Orders")),
                    _sidebar_link("orders_material", _("Materials")),
                ],
            },
            {
                "title": _("Production"),
                "separator": True,
                "items": [
                    _sidebar_link("production_employee", _("Employees")),
                    _sidebar_link("production_productionstage", _("Stages")),
                    _sidebar_link("production_ticket", _("Tickets")),
                    _sidebar_link("production_statushistory", _("Status history")),
                    _sidebar_link("production_delivery", _("Deliveries")),
                ],
            },
            {
                "title": _("Reports"),
                "separator": True,
                "items": [
                    {
                        "title": _("Admin dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
        ],
    },
    "COLORS": {
        "primary": {
            "50": "#fdf6f4",
            "100": "#fceee9",
            "200": "#f8d8cf",
            "300": "#f2b8a8",
            "400": "#e88d75",
            "500": "#C84B31",
            "600": "#a93d28",
            "700": "#8c3321",
            "800": "#6f281a",
            "900": "#4a1b12",
            "950": "#2f100b",
        },
    },
    "DASHBOARD_CALLBACK": "sewing_shop.dashboard.dashboard_callback",
    # Each entry must include ``link`` — Unfold's dropdown is flat (no nested ``items``).
    "SITE_DROPDOWN": [
        {
            "title": _("Spanish"),
            "icon": "translate",
            "link": reverse_lazy("switch_language", kwargs={"language": "es"}),
        },
        {
            "title": _("English"),
            "icon": "translate",
            "link": reverse_lazy("switch_language", kwargs={"language": "en"}),
        },
    ],
}
