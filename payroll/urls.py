from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [

    path("<slug:country_slug>/<int:company_id>/payroll", views.payroll, name="payroll"),
    path("<slug:country_slug>/<int:company_id>/payroll/create/", views.payroll_create, name="payroll_create"),
    path("<slug:country_slug>/<int:company_id>/payroll/edit/<int:pk>/", views.payroll_edit, name="payroll_edit"),
    path("<slug:country_slug>/<int:company_id>/payroll/delete/<int:pk>/", views.payroll_delete, name="payroll_delete"),

]


