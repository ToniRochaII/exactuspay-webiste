from django.urls import path
from . import views

app_name = "pdcodes"

urlpatterns = [
    path(
        "<slug:country_slug>/<int:company_id>/pdcodes/",
        views.pdcode_list,
        name="pdcodes",
    ),
    path(
        "<slug:country_slug>/<int:company_id>/pdcodes/create/",
        views.pdcode_create,
        name="pdcode_create",
    ),
    path(
        "<slug:country_slug>/<int:company_id>/pdcodes/edit/<str:pdcode_code>/",
        views.pdcode_edit,
        name="pdcode_edit",
    ),
    path(
        "<slug:country_slug>/<int:company_id>/pdcodes/delete/<str:pdcode_code>/",
        views.pdcode_delete,
        name="pdcode_delete",
    ),
]
