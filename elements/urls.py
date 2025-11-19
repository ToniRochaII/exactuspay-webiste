from django.urls import path
from . import views

app_name = "elements"

urlpatterns = [

    path("<slug:country_slug>/elements/", views.element, name="elements"),
    path("<slug:country_slug>/elements/create/", views.element_create, name="element_create"),
    path("<slug:country_slug>/elements/edit/<int:element_code>/", views.element_edit, name="element_edit"),
    path("<slug:country_slug>/elements/delete/<int:element_code>/", views.element_delete, name="element_delete"),

]


