from django.urls import path
from . import views

app_name = "payregister"

urlpatterns = [
    # List all pay register entries for a company
    path("<slug:country_slug>/<int:company_id>/payregister/", 
         views.payregister_list, 
         name="payregister_list"),
    
    # Create new pay register entry
    path("<slug:country_slug>/<int:company_id>/payregister/create/", 
         views.payregister_create, 
         name="payregister_create"),
    
    # Edit specific pay register entry
    path("<slug:country_slug>/<int:company_id>/payregister/<int:id>/edit/", 
         views.payregister_edit, 
         name="payregister_edit"),
    
    # Delete specific pay register entry
    path("<slug:country_slug>/<int:company_id>/payregister/<int:id>/delete/", 
         views.payregister_delete, 
         name="payregister_delete"),
    
    # View pay register entries for a specific employee
    path("<slug:country_slug>/<int:company_id>/payregister/employee/<int:employee_id>/", 
         views.payregister_by_employee, 
         name="payregister_by_employee"),
]