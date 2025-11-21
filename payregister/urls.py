from django.urls import path
from . import views

app_name = "payregister"

urlpatterns = [
    path("<slug:country_slug>/<int:company_id>/payregister/<int:id>/",views.list_entries,name="payregister_list",),
    path("<slug:country_slug>/<int:company_id>/payregister/<int:id>/create/",views.create_entry,name="payregister_create",),
]

