from django.urls import path
from . import views

app_name = "country"

urlpatterns = [

    path("", views.country, name="country"),
    path("create/", views.country_create, name="country_create"),
    path("delete/", views.country_delete, name="country_delete"),
    path("<slug:slug>/edit/", views.country_edit, name="country_edit"),




]
