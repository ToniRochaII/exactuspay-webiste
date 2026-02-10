# employee/urls.py - Update the upload route
from django.urls import path
from Exactus.employee import views

app_name = "employee"

urlpatterns = [
    path("<slug:country_slug>/<int:company_id>/", views.employee_list, name="employee"),
    path("<slug:country_slug>/<int:company_id>/create/", views.employee_create, name="employee_create"),
    path("<slug:country_slug>/<int:company_id>/edit/<int:employee_id>/", views.employee_edit, name="employee_edit"),
    
    # Updated upload routes using class-based view
    path("<slug:country_slug>/<int:company_id>/upload/", views.EmployeeUploadView.as_view(), name="employee_upload"),
    path("<slug:country_slug>/<int:company_id>/upload/result/", views.employee_upload_result_view, name="employee_upload_result"),
    path("<slug:country_slug>/<int:company_id>/upload/template/", views.download_employees_template, name="download_employees_template"),

    path("<slug:country_slug>/<int:company_id>/edit/<int:employee_id>/", views.employee_edit, name="employee_edit"),
    
    path("<slug:country_slug>/<int:company_id>/edit/<int:employee_id>/compensation/", views.employee_compensation, name="employee_compensation"),


        # ────────────────────────────────────────────────
    # GLOBAL ROUTES (Now correctly named for the template tag)
    # ────────────────────────────────────────────────
    path("<slug:country_slug>/employee/upload/", views.EmployeeUploadView.as_view(), name="global_upload"),
    path("<slug:country_slug>/employee/upload/result/", views.global_upload_result_view, name="global_upload_result"),
    
    # ADDED: This allows a template download without a company_id
    path("<slug:country_slug>/employee/upload/template/", 
         views.download_employees_template, 
         name="download_employees_template_global"),

    # ────────────────────────────────────────────────
    # COUNTRY/COMPANY SPECIFIC ROUTES
    # ────────────────────────────────────────────────
    # ... other paths ...
    path("<slug:country_slug>/<int:company_id>/upload/template/", 
         views.download_employees_template, 
         name="download_employees_template"),
]