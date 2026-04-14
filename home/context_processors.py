from __future__ import annotations

from django.conf import settings


def site_context(request):
    return {
        "external_payroll_login_url": settings.EXTERNAL_PAYROLL_LOGIN_URL,
        "book_demo_external_url": settings.BOOK_DEMO_EXTERNAL_URL,
    }
