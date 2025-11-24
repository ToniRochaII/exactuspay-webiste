# elements/urls.py
from django.urls import path
from . import views

app_name = "elements"

urlpatterns = [
    # Listing, CRUD
    path("<slug:country_slug>/elements/", views.element, name="elements"),
    path("<slug:country_slug>/elements/create/", views.element_create, name="element_create"),
    path("<slug:country_slug>/elements/<str:element_code>/edit/", views.element_edit, name="element_edit"),
    path("<slug:country_slug>/elements/<str:element_code>/delete/", views.element_delete, name="element_delete"),

    # Upload
    path("<slug:country_slug>/elements/upload/", views.element_upload_view, name="elements_upload"),
    path("elements/upload/", views.element_upload_view, name="elements_upload_global"),

    # Upload results
    path("<slug:country_slug>/elements/upload/result/", views.element_upload_result_view, name="elements_upload_result"),
    path("elements/upload/result/", views.element_upload_result_view, name="elements_upload_result_global"),

    # Template download
    path("<slug:country_slug>/elements/upload/template/", views.download_elements_template, name="download_elements_template"),
    path("elements/upload/template/", views.download_elements_template, name="download_elements_template_global"),
]
