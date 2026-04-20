from __future__ import annotations

from django.conf import settings
from django.utils.translation import get_language_info


LANGUAGE_FLAGS = {
    "ar": "🇸🇦",
    "de": "🇩🇪",
    "en": "🇬🇧",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "id": "🇮🇩",
    "it": "🇮🇹",
    "pl": "🇵🇱",
    "pt": "🇧🇷",
    "ru": "🇷🇺",
    "sw": "🇹🇿",
    "th": "🇹🇭",
}


def _build_public_languages():
    public_languages = []
    for code, fallback_label in settings.LANGUAGES:
        info = get_language_info(code)
        public_languages.append(
            {
                "code": code,
                "flag": LANGUAGE_FLAGS.get(code, "🌐"),
                "label": info.get("name_local") or fallback_label,
            }
        )
    return public_languages


def site_context(request):
    return {
        "external_payroll_login_url": settings.EXTERNAL_PAYROLL_LOGIN_URL,
        "book_demo_external_url": settings.BOOK_DEMO_EXTERNAL_URL,
        "supported_language_codes": [code for code, _label in settings.LANGUAGES],
        "public_languages": _build_public_languages(),
    }
