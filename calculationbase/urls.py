from django.urls import path
from . import views

app_name = "calculationbase"

urlpatterns = [
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/", views.calculationbase_list, name="list"),
    path("<slug:country_slug>/calculationbase/<int:regulations_id>/create/", views.calculationbase_create, name="create"),
    path("<slug:country_slug>/calculationbase/edit/<int:pk>/", views.calculationbase_edit, name="edit"),
    path("<slug:country_slug>/calculationbase/delete/<int:pk>/", views.calculationbase_delete, name="delete"),
]
