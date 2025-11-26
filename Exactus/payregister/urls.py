# payregister/urls.py
from django.urls import path
from . import views

app_name = "payregister"

urlpatterns = [
    
    path("<slug:country_slug>/<int:company_id>/payregister/<int:id>/",views.list_entries, name="payregister_list"),
    path("<slug:country_slug>/<int:company_id>/payregister/<int:id>/create/",views.create_entry, name="payregister_create"),

    # NEW BULK UPLOAD ROUTES
    path("<slug:country_slug>/<int:company_id>/payregister/upload/",views.payregister_upload_view, name="payregister_upload"),
    path("<slug:country_slug>/<int:company_id>/payregister/upload/result/",views.payregister_upload_result_view, name="payregister_upload_result"),
    path("<slug:country_slug>/<int:company_id>/payregister/upload/template/",views.download_payregister_template, name="payregister_upload_template"),
]
