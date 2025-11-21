from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [

    path("<slug:country_slug>/<int:company_id>/", views.payroll_list, name="payroll"),
    path("<slug:country_slug>/<int:company_id>/create/", views.payroll_create, name="payroll_create"),
    path("<slug:country_slug>/<int:company_id>/edit/<int:payroll_id>/", views.payroll_edit, name="payroll_edit"),
    path("<slug:country_slug>/<int:company_id>/delete/<int:payroll_id>/", views.payroll_delete, name="payroll_delete"),

]


