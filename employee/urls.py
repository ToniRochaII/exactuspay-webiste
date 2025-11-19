from django.urls import path
from . import views

app_name = "employee"

urlpatterns = [

    path("<int:company_id>/", views.employee_list, name="employee"),
    path("<int:company_id>/create/", views.employee_create, name="employee_create"),
    path("<int:company_id>/edit/<int:employee_id>/", views.employee_edit, name="employee_edit"),

]
