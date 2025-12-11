# Exactus/payroll/urls.py - Add these URL patterns
from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # Dashboard
    path('<slug:country_slug>/<int:company_id>/payroll/dashboard/', 
         views.payroll_dashboard, 
         name='payroll_dashboard'),
    
    # Payroll URLs
    path('<slug:country_slug>/<int:company_id>/payroll/',
         views.PayrollListView.as_view(),
         name='payroll_list'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/create/',
         views.PayrollCreateView.as_view(),
         name='payroll_create'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:pk>/',
         views.PayrollDetailView.as_view(),
         name='payroll_detail'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:pk>/edit/',
         views.PayrollUpdateView.as_view(),
         name='payroll_edit'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:pk>/delete/',
         views.PayrollDeleteView.as_view(),
         name='payroll_delete'),
    
    # AJAX actions for payroll
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/lock/',
         views.lock_payroll,
         name='payroll_lock'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/unlock/',
         views.unlock_payroll,
         name='payroll_unlock'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/summary/',
         views.payroll_summary_api,
         name='payroll_summary_api'),
    
    # Period URLs
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/',
         views.PayrollPeriodListView.as_view(),
         name='period_list'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/create/',
         views.PayrollPeriodCreateView.as_view(),
         name='period_create'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:pk>/',
         views.PayrollPeriodDetailView.as_view(),
         name='period_detail'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:pk>/edit/',
         views.PayrollPeriodUpdateView.as_view(),
         name='period_edit'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:pk>/delete/',
         views.PayrollPeriodDeleteView.as_view(),
         name='period_delete'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/process/',
         views.PayrollPeriodProcessView.as_view(),
         name='period_process'),
    
    # AJAX actions for periods
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/lock/',
         views.lock_period,
         name='period_lock'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/unlock/',
         views.unlock_period,
         name='period_unlock'),
    
    # Utility endpoints
    path('api/payroll/<int:payroll_id>/next-period_number/',
         views.get_next_period_number,
         name='next_period_number'),
]