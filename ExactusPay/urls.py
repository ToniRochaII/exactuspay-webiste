from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # needed for set_language
]

urlpatterns += i18n_patterns(
    path("", include("home.urls")),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    prefix_default_language=False,
)
