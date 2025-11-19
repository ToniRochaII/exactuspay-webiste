from django.urls import path
from . import views

app_name = "employee"

urlpatterns = [

    path("<slug:country_slug>/", views.employee_list, name="employee"),
    path("<slug:country_slug>/create/", views.employee_create, name="employee_create"),
    path("<slug:country_slug>/edit/<int:employee_id>/", views.employee_edit, name="employee_edit"),

]
