from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include("apps.api.urls")),
    path("api/auth/", include("apps.api.auth_urls")),
]
