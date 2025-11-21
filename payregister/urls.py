from django.urls import path
from . import views

app_name = "payregister"

urlpatterns = [
    path(
        "payregister/<int:employee_id>/",
        views.list_entries,
        name="payregister_list",
    ),
    path(
        "payregister/<int:employee_id>/create/",
        views.create_entry,
        name="payregister_create",
    ),
]

