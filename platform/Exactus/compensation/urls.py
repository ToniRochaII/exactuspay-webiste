# Exactus/compensation/urls.py
from django.urls import path
from Exactus.compensation import views

app_name = "compensation"

urlpatterns = [
    path(
        "<slug:country_slug>/<int:company_id>/employee/<int:employee_id>/",
        views.compensation_list,
        name="compensation_list",
    ),
    path(
        "<slug:country_slug>/<int:company_id>/employee/<int:employee_id>/create/",
        views.compensation_create,
        name="compensation_create",
    ),
    path(
        "<slug:country_slug>/<int:company_id>/employee/<int:employee_id>/<int:component_id>/edit/",
        views.compensation_edit,
        name="compensation_edit",
    ),
    path(
        "<slug:country_slug>/<int:company_id>/employee/<int:employee_id>/<int:component_id>/delete/",
        views.compensation_delete,
        name="compensation_delete",
    ),

    path('<slug:country_slug>/<int:company_id>/compensation/upload/', views.compensation_upload_view, name='compensation_upload'),
    path('<slug:country_slug>/<int:company_id>/compensation/upload/result/', views.compensation_upload_result_view, name='compensation_upload_result'),
    path('<slug:country_slug>/<int:company_id>/compensation/template/', views.download_compensation_template, name='download_compensation_template'),




]
