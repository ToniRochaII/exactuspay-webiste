# company/urls.py
from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("<slug:country_slug>/", views.company, name="company"),
    path("<slug:country_slug>/create/", views.company_create, name="company_create"),
    path("<slug:country_slug>/delete", views.company_delete, name="company_delete"),
    path("<slug:country_slug>/edit/<int:company_id>/", views.company_edit, name="company_edit"),
    
    # Upload routes - country specific
    path("<slug:country_slug>/upload/", views.company_upload_view, name="company_upload"),
    path("<slug:country_slug>/upload/result/", views.company_upload_result_view, name="company_upload_result"),
    path("<slug:country_slug>/upload/template/", views.download_companies_template, name="download_companies_template"),
    
    # Global upload routes (optional)
    path("company/upload/", views.company_upload_view, name="company_upload_global"),
    path("company/upload/result/", views.company_upload_result_view, name="company_upload_result_global"),
    path("company/upload/template/", views.download_companies_template, name="download_companies_template_global"),
]