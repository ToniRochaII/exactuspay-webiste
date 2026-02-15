from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("home.urls")),
    path("admin/", admin.site.urls),
]
