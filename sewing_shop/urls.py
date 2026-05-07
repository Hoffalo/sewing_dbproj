from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.production import views as production_views
from sewing_shop import views as sewing_views

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", query_string=True)),
    # Django's i18n view (POST `/i18n/setlang/`) — name must be ``set_language`` for Unfold's language form.
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path(
        "admin/production/ticket/<int:ticket_id>/pdf/",
        admin.site.admin_view(production_views.ticket_pdf),
        name="production_ticket_pdf",
    ),
    # GET language switcher for ``SITE_DROPDOWN`` (do not reuse name ``set_language``).
    path(
        "set-language/<str:language>/",
        sewing_views.switch_language,
        name="switch_language",
    ),
]
