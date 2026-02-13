from django.urls import path
from .views import (
    # Dashboards
    SystemReportDashboard, 
    CountryReportDashboard, 
    CompanyReportDashboard,
    GenerateReportView,
    
    # Management Hub
    ReportManagementHub,
    
    # CRUD: Report Types
    ReportTypeListView, ReportTypeCreateView, ReportTypeUpdateView, ReportTypeDeleteView,
    
    # CRUD: Report Layouts
    ReportLayoutListView, ReportLayoutCreateView, ReportLayoutUpdateView, ReportLayoutDeleteView,
    
    # CRUD: Configurations
    ReportConfigListView, ReportConfigCreateView, ReportConfigUpdateView, ReportConfigDeleteView
)

# This registers the namespace so templates can use {% url 'reports:...' %}
app_name = 'reports'

urlpatterns = [
    # --- DASHBOARDS (User Facing) ---
    path('reports/', SystemReportDashboard.as_view(), name='reports_system_dashboard'),
    path('<slug:country_slug>/reports/', CountryReportDashboard.as_view(), name='reports_country_dashboard'),
    
    # Renamed to 'list' to match base.html: {% url 'reports:list' country_slug company.company_id %}
    path('<slug:country_slug>/<int:company_id>/reports/', CompanyReportDashboard.as_view(), name='list'),

    # --- GENERATOR (The Engine) ---
    # Added route for 'run' to match base.html: {% url 'reports:run' country_slug company.company_id report_id %}
    path('<slug:country_slug>/<int:company_id>/run/<str:report_code>/', GenerateReportView.as_view(), name='run'),
    
    # Original generation routes (kept for backwards compatibility)
    path('generate/<str:report_code>/<int:company_id>/', GenerateReportView.as_view(), name='generate_report'),
    path('generate/<str:report_code>/', GenerateReportView.as_view(), name='generate_system_report'),

    # --- MANAGEMENT SYSTEM (Admin Facing) ---
    path('manage/', ReportManagementHub.as_view(), name='report_manage_hub'),
    
    # Manage Types
    path('manage/types/', ReportTypeListView.as_view(), name='manage_types_list'),
    path('manage/types/add/', ReportTypeCreateView.as_view(), name='manage_types_add'),
    path('manage/types/<int:pk>/edit/', ReportTypeUpdateView.as_view(), name='manage_types_edit'),
    path('manage/types/<int:pk>/delete/', ReportTypeDeleteView.as_view(), name='manage_types_delete'),

    # Manage Layouts
    path('manage/layouts/', ReportLayoutListView.as_view(), name='manage_layouts_list'),
    path('manage/layouts/add/', ReportLayoutCreateView.as_view(), name='manage_layouts_add'),
    path('manage/layouts/<int:pk>/edit/', ReportLayoutUpdateView.as_view(), name='manage_layouts_edit'),
    path('manage/layouts/<int:pk>/delete/', ReportLayoutDeleteView.as_view(), name='manage_layouts_delete'),

    # Manage Configurations
    path('manage/configs/', ReportConfigListView.as_view(), name='manage_configs_list'),
    path('manage/configs/add/', ReportConfigCreateView.as_view(), name='manage_configs_add'),
    path('manage/configs/<int:pk>/edit/', ReportConfigUpdateView.as_view(), name='manage_configs_edit'),
    path('manage/configs/<int:pk>/delete/', ReportConfigDeleteView.as_view(), name='manage_configs_delete'),
]