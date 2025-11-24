# employee/urls.py
from django.urls import path
from . import views

app_name = "employee"

urlpatterns = [
    path("<slug:country_slug>/<int:company_id>/", views.employee_list, name="employee"),
    path("<slug:country_slug>/<int:company_id>/create/", views.employee_create, name="employee_create"),
    path("<slug:country_slug>/<int:company_id>/edit/<int:employee_id>/", views.employee_edit, name="employee_edit"),
    
    # Upload routes
    path("<slug:country_slug>/<int:company_id>/upload/", views.employee_upload_view, name="employee_upload"),
    path("<slug:country_slug>/<int:company_id>/upload/result/", views.employee_upload_result_view, name="employee_upload_result"),
    path("<slug:country_slug>/<int:company_id>/upload/template/", views.download_employees_template, name="download_employees_template"),

     path("employee/upload/progress/", views.upload_progress, name="upload_progress"),
]