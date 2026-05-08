from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation


def switch_language(request, language: str):
    """GET shortcut for navbar links — sets cookie and redirects back."""
    allowed = {code for code, _ in settings.LANGUAGES}
    language = language if language in allowed else settings.LANGUAGE_CODE
    translation.activate(language)
    redirect_to = request.META.get("HTTP_REFERER") or "/admin/"
    response = HttpResponseRedirect(redirect_to)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
    )
    return response
