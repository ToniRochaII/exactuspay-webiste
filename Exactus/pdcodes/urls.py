# pdcodes/urls.py - Update the urlpatterns
from django.urls import path
from Exactus.pdcodes import views

app_name = "pdcodes"

urlpatterns = [

    path("<slug:country_slug>/<int:company_id>/pdcodes/",views.pdcode_list,name="pdcodes",),
    path("<slug:country_slug>/<int:company_id>/pdcodes/create/",views.pdcode_create,name="pdcode_create",),
    path("<slug:country_slug>/<int:company_id>/pdcodes/edit/<str:pdcode_code>/",views.pdcode_edit,name="pdcode_edit",),
    path("<slug:country_slug>/<int:company_id>/pdcodes/delete/<str:pdcode_code>/",views.pdcode_delete,name="pdcode_delete",),
    
    # Upload routes
    path("<slug:country_slug>/<int:company_id>/pdcodes/upload/", views.pdcode_upload_view,name="pdcode_upload",),
    path("<slug:country_slug>/<int:company_id>/pdcodes/upload/result/",views.pdcode_upload_result_view,name="pdcode_upload_result",),
    path("<slug:country_slug>/<int:company_id>/pdcodes/upload/template/",views.download_pdcodes_template,name="download_pdcodes_template",),
         
    path("<slug:country_slug>/pdcodes/upload/country/",views.pdcode_upload_country_view, name="pdcode_upload_country",),
    path("<slug:country_slug>/pdcodes/upload/country/result/", views.pdcode_upload_country_result_view, name="pdcode_upload_country_result",),


]