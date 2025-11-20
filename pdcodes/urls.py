from django.urls import path
from . import views

app_name = "pdcodes"

urlpatterns = [

    path("<int:company_id>/pdcodes/", views.pdcode, name="pdcodes"),
    path("<int:company_id>/pdcodes/create/", views.pdcode_create, name="pdcode_create"),
    path("<int:company_id>/pdcodes/edit/<int:pdcode_code>/", views.pdcode_edit, name="pdcode_edit"),
    path("<int:company_id>/pdcodes/delete/<int:pdcode_code>/", views.pdcode_delete, name="pdcode_delete"),

]


