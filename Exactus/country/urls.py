from django.urls import path
from Exactus.country import views

app_name = "country"

urlpatterns = [

    path("country/", views.country, name="country"),
    path("country/create/", views.country_create, name="country_create"),
    path("delete/", views.country_delete, name="country_delete"),
    path("<slug:slug>/edit/", views.country_edit, name="country_edit"),

    path("country/upload/", views.country_upload_view, name="country_upload"),
    path("country/upload/result/", views.country_upload_result_view, name="country_upload_result"),
    path("country/upload/template/", views.download_csv_template, name="download_csv_template"),

    path('dashboard_country_map/', views.dashboard_country_map, name='dashboard_country_map'),

]
