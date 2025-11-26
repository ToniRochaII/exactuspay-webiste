from django.urls import path
from . import views

app_name = "country"

urlpatterns = [

    path("country/", views.country, name="country"),
    path("country/create/", views.country_create, name="country_create"),
    path("<slug:slug>/delete/", views.country_delete, name="country_delete"),
    path("<slug:slug>/edit/", views.country_edit, name="country_edit"),

    path("country/upload/", views.country_upload_view, name="country_upload"),
    path("country/upload/result/", views.country_upload_result_view, name="country_upload_result"),
    path("country/upload/template/", views.download_csv_template, name="download_csv_template"),

]
