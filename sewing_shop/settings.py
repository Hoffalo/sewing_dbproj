"""
Django settings for Costuras Lucía — sewing shop management (course project).
Spanish-first UI with English toggle; PostgreSQL + Django Unfold admin.
"""

from pathlib import Path
import os

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static

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


UNFOLD = {
    "SITE_TITLE": "Costuras Lucía",
    "SITE_HEADER": "Costuras Lucía",
    "SITE_SUBHEADER": _("Sastrería · Madrid"),
    "SITE_SYMBOL": "checkroom",
    "SHOW_LANGUAGES": True,
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "THEME": "light",
    "LOGIN": {
        "image": lambda request: static("img/login_bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [
        lambda request: static("css/unfold_overrides.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/force_light_theme.js"),
    ],
    "COLORS": {
        # Neutral whites / gray — dominates the UI (“primary” atmosphere).
        "base": {
            "50": "255 255 255",
            "100": "250 251 252",
            "200": "241 243 246",
            "300": "228 231 237",
            "400": "201 207 217",
            "500": "142 148 162",
            "600": "98 106 122",
            "700": "70 76 93",
            "800": "50 54 67",
            "900": "35 39 51",
            "950": "22 25 34",
        },
        # Lavender — darker ramp for readability on white.
        "primary": {
            "50": "250 248 252",
            "100": "240 236 246",
            "200": "220 209 237",
            "300": "196 174 219",
            "400": "168 146 195",
            "500": "140 117 169",
            "600": "115 93 146",
            "700": "92 73 118",
            "800": "72 56 94",
            "900": "52 39 71",
            "950": "34 26 52",
        },
        "font": {
            "subtle-light": "var(--color-primary-800)",
            "subtle-dark": "var(--color-primary-500)",
            "default-light": "var(--color-primary-950)",
            "default-dark": "var(--color-primary-200)",
            "important-light": "var(--color-primary-950)",
            "important-dark": "var(--color-primary-50)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Operations"),
                "separator": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Customers"),
                        "icon": "person",
                        "link": reverse_lazy("admin:customers_customer_changelist"),
                    },
                    {
                        "title": _("Orders"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:orders_order_changelist"),
                    },
                    {
                        "title": _("CRM pipeline"),
                        "icon": "view_kanban",
                        "link": reverse_lazy("admin:orders_order_crm_board"),
                    },
                    {
                        "title": _("Tickets"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:production_ticket_changelist"),
                    },
                    {
                        "title": _("Deliveries"),
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:production_delivery_changelist"),
                    },
                ],
            },
            {
                "title": _("Catalog"),
                "separator": True,
                "items": [
                    {
                        "title": _("Materials"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:orders_material_changelist"),
                    },
                    {
                        "title": _("Production stages"),
                        "icon": "timeline",
                        "link": reverse_lazy("admin:production_productionstage_changelist"),
                    },
                ],
            },
            {
                "title": _("Team"),
                "separator": True,
                "items": [
                    {
                        "title": _("Employees"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:production_employee_changelist"),
                    },
                    {
                        "title": _("Users"),
                        "icon": "key",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                ],
            },
        ],
    },
    "DASHBOARD_CALLBACK": "apps.production.dashboard.dashboard_callback",
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
