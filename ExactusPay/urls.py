import re

from django.conf import settings
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # needed for set_language
]

urlpatterns += i18n_patterns(
    path("", include("home.urls")),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    prefix_default_language=False,
)

if settings.SERVE_MEDIA_FILES and settings.MEDIA_URL:
    media_prefix = re.escape(settings.MEDIA_URL.lstrip("/"))
    urlpatterns += [
        re_path(
            rf"^{media_prefix}(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]
