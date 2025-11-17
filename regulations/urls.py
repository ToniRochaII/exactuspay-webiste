from django.urls import path
from . import views

app_name = "regulations"

urlpatterns = [

    path("<slug:country_slug>/regulations/", views.regulations, name="regulations"),
    path("<slug:country_slug>/regulations/create/", views.regulations_create, name="regulations_create"),
    path("<slug:country_slug>delete/regulations/<int:regulations_id>/", views.regulations_delete, name="regulations_delete"),
    path("<slug:country_slug>/edit/regulations/<int:regulations_id>/", views.regulations_edit, name="regulations_edit"),

]

