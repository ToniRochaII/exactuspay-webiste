from django.urls import path
from . import views

app_name = 'ess'

urlpatterns = [
    # Main Employee Self-Service Dashboard
    path('ess/dashboard/', views.employee_self_service, name='dashboard'),
    
    # Specific view for downloading/viewing a payslip PDF
    path('ess/payslip/<int:result_id>/', views.view_payslip, name='view_payslip'),
]