from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # ========================================================
    # DASHBOARD
    # ========================================================
    path('<slug:country_slug>/<int:company_id>/dashboard/', 
         views.payroll_dashboard, 
         name='payroll_dashboard'),

    # ========================================================
    # PAYROLL CRUD
    # ========================================================
    path('<slug:country_slug>/<int:company_id>/payrolls/', 
         views.PayrollListView.as_view(), 
         name='payroll_list'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/add/', 
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
    
    # ========================================================
    # PAYROLL ACTIONS (RESET & LOCKING)
    # ========================================================
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/reset/', 
         views.payroll_reset_confirm, 
         name='payroll_reset'),


    # AJAX: Lock/Unlock Payroll
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/lock/', 
         views.lock_payroll, 
         name='lock_payroll'),
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/unlock/', 
         views.unlock_payroll, 
         name='unlock_payroll'),

    # ========================================================
    # PERIOD CRUD
    # ========================================================
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/periods/', 
         views.PayrollPeriodListView.as_view(), 
         name='period_list'),
    
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/add/', 
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

    # ========================================================
    # PERIOD PROCESSING & ACTIONS
    # ========================================================
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/process/', 
         views.PayrollPeriodProcessView.as_view(), 
         name='period_process'),
         
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/approve/', 
         views.approve_period, 
         name='approve_period'),
         
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/reset/', 
         views.payroll_period_reset_confirm, 
         name='period_reset'),
         
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/export/', 
         views.PayrollPeriodExportView.as_view(), 
         name='period_export'),

    # AJAX: Lock/Unlock Period
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/lock/', 
         views.lock_period, 
         name='lock_period'),
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/unlock/', 
         views.unlock_period, 
         name='unlock_period'),
    
    # ========================================================
    # UTILITIES & APIs
    # ========================================================
    path('<slug:country_slug>/<int:company_id>/payroll/<int:payroll_id>/period/<int:period_id>/audit-base/', 
         views.payroll_base_audit, 
         name='base_audit'),

    path('api/payroll/<int:payroll_id>/summary/', 
         views.payroll_summary_api, 
         name='payroll_summary_api'),

    # --- THIS WAS THE MISSING URL ---
    path('api/payroll/<int:payroll_id>/next-period/', 
         views.get_next_period_number, 
         name='next_period_number'),
]