# Exactus/calculationbase/urls.py
from django.urls import path
from django.views.generic import TemplateView
from Exactus.calculationbase import views

app_name = "calculationbase"

urlpatterns = [
    # --- Global Routes (No Country, No Regulation) ---
    path(
        "global-tools/",
        TemplateView.as_view(template_name="global_tools.html"),
        name="global_tools",
    ),
    path("calculationbase/upload/", views.calculationbase_upload, name="upload_global"),
    path("calculationbase/upload/result/", views.calculationbase_upload_result, name="upload_result_global"),
    path("calculationbase/template/", views.download_calculationbase_template, name="download_template_global"),

    # --- Country Scope Routes (Country Known, Regulation inferred from CSV) ---
    # [ADDED] This fixes your 404 error
    path(
        "<slug:country_slug>/calculationbase/upload/", 
        views.calculationbase_upload, 
        name="upload_country_scope"
    ),
    path(
        "<slug:country_slug>/calculationbase/upload/result/", 
        views.calculationbase_upload_result, 
        name="upload_result_country_scope"
    ),
    path(
        "<slug:country_slug>/calculationbase/template/", 
        views.download_calculationbase_template, 
        name="download_template_country_scope"
    ),

    # --- Regulation Scope Routes (Country Known, Regulation Known) ---
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/", views.calculationbase_list, name="list"),
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/create/", views.calculationbase_create, name="create"),
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/<int:pk>/edit/", views.calculationbase_edit, name="edit"),
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/<int:pk>/delete/", views.calculationbase_delete, name="delete"),
    
    # Local Upload (Specific to a regulation)
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/upload/", views.calculationbase_upload, name="upload"),
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/upload/result/", views.calculationbase_upload_result, name="upload_result"),
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/template/", views.download_calculationbase_template, name="download_template"),
]