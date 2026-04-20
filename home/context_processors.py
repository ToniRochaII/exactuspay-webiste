from __future__ import annotations

from django.conf import settings
from django.utils.translation import gettext as _


def site_context(request):
    return {
        "external_payroll_login_url": settings.EXTERNAL_PAYROLL_LOGIN_URL,
        "book_demo_external_url": settings.BOOK_DEMO_EXTERNAL_URL,
        "supported_language_codes": [code for code, _label in settings.LANGUAGES],
        "public_languages": [
            {"code": "en", "flag": "🇬🇧", "label": _("English")},
            {"code": "pt", "flag": "🇧🇷", "label": _("Portuguese")},
            {"code": "es", "flag": "🇪🇸", "label": _("Spanish")},
        ],
    }
