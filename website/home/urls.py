from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="home"),
    
    path("platform/", views.platform, name="platform"),

    path("features/", views.features, name="features"),

    path("security/", views.security, name="security"),

    path("pricing/", views.pricing, name="pricing"),

    path("resources/", views.resources, name="resources"),

    path("demo/", views.demo_page, name="demo"),
    
    path("demo/request/", views.demo_request, name="demo_request"),
]
