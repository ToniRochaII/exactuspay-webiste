from django.urls import path
from Exactus.regulations import views

app_name = "regulations"

urlpatterns = [
    path("<slug:country_slug>/regulations/", views.regulations, name="regulations"),
    path("<slug:country_slug>/regulations/create/", views.regulations_create, name="regulations_create"),
    path("<slug:country_slug>/delete/regulations/<int:regulations_id>/", views.regulations_delete, name="regulations_delete"),
    path("<slug:country_slug>/edit/regulations/<int:regulations_id>/", views.regulations_edit, name="regulations_edit"),
    
    # Upload routes - country specific
    path("<slug:country_slug>/regulations/upload/", views.regulations_upload_view, name="regulations_upload"),
    path("<slug:country_slug>/regulations/upload/result/", views.regulations_upload_result_view, name="regulations_upload_result"),
    path("<slug:country_slug>/regulations/upload/template/", views.download_regulations_template, name="download_regulations_template"),
    
    # Global upload routes (optional)
    path("regulations/upload/", views.regulations_upload_view, name="regulations_upload_global"),
    path("regulations/upload/result/", views.regulations_upload_result_view, name="regulations_upload_result_global"),
    path("regulations/upload/template/", views.download_regulations_template, name="download_regulations_template_global"),
]
