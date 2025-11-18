from django.urls import path
from . import views

app_name = "calculationbase"

urlpatterns = [
    path("<int:country_id>/<int:regulations_id>/", views.calculationbase_list, name="list"),
    path("<int:country_id>/<int:regulations_id>/create/", views.calculationbase_create, name="create"),
    path("<int:country_id>/<int:regulations_id>/edit/<int:pk>/", views.calculationbase_edit, name="edit"),
    path("<int:country_id>/<int:regulations_id>/delete/<int:pk>/", views.calculationbase_delete, name="delete"),
]
