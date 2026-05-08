from decimal import Decimal

from babel.numbers import format_currency
from django.utils.translation import get_language


def format_money(amount: Decimal | int | float, currency: str) -> str:
    """Format an amount for display in the active locale."""
    if amount is None:
        return ""
    lang = get_language() or "es"
    locale = {"es": "es_ES", "en": "en_US"}.get(lang[:2], "es_ES")
    return format_currency(Decimal(amount), currency, locale=locale)
