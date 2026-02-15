from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # needed for set_language
    path("", include("home.urls")),
    path("admin/", admin.site.urls),
]
