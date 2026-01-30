from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # List all reports for a company
    # URL: /123/reports/
    path('<country_slug>/<int:company_id>/reports/', views.report_list, name='list'),
    path('<slug:country_slug>/<int:company_id>/payslips/', views.payslip_run, name='payslip_run'),

    # Run a specific report
    # URL: /123/reports/45/run/
    path('<country_slug>/<int:company_id>/reports/<int:report_id>/run/', views.report_run, name='run'),
    path('<slug:country_slug>/<int:company_id>/reports/rti/', views.rti_run, name='rti_run'),
]