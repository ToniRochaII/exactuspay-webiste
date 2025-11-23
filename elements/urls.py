# elements/urls.py
from django.urls import path
from . import views

app_name = "elements"

urlpatterns = [
    path("<slug:country_slug>/elements/", views.element, name="elements"),
    path("<slug:country_slug>/elements/create/", views.element_create, name="element_create"),
    path("<slug:country_slug>/elements/edit/<str:element_code>/", views.element_edit, name="element_edit"),
    path("<slug:country_slug>/elements/delete/<str:element_code>/", views.element_delete, name="element_delete"),
    
    # Upload routes - country specific
    path("<slug:country_slug>/elements/upload/", views.element_upload_view, name="elements_upload"),
    path("<slug:country_slug>/elements/upload/result/", views.element_upload_result_view, name="elements_upload_result"),
    path("<slug:country_slug>/elements/upload/template/", views.download_elements_template, name="download_elements_template"),
    
    # Global upload routes (optional)
    path("elements/upload/", views.element_upload_view, name="elements_upload_global"),
    path("elements/upload/result/", views.element_upload_result_view, name="elements_upload_result_global"),
    path("elements/upload/template/", views.download_elements_template, name="download_elements_template_global"),
]