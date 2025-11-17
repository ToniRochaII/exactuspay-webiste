from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [

    path("<slug:country_slug>/", views.company, name="company"),
    path("<slug:country_slug>/create/", views.company_create, name="company_create"),
    path("<slug:country_slug>delete/<int:company_id>/", views.company_delete, name="company_delete"),
    path("<slug:country_slug>/edit/<int:company_id>/", views.company_edit, name="company_edit"),

]
