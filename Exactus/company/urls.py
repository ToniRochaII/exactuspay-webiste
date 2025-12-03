"""
Company URL Configuration
"""

from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Company management
    path('<slug:country_slug>/', views.company_list, name='company_list'),
    path('<slug:country_slug>/create/', views.company_create, name='company_create'),
    path('<slug:country_slug>/edit/<int:company_id>/', views.company_edit, name='company_edit'),
    path('<slug:country_slug>/delete/<int:company_id>/', views.company_delete, name='company_delete'),
    
    # Bulk operations
    path('<slug:country_slug>/upload/', views.company_upload, name='company_upload'),
    path('<slug:country_slug>/upload/result/', views.company_upload_result, name='company_upload_result_country'),
    path('<slug:country_slug>/download-template/', views.download_companies_template, name='download_template'),
    
    # Global operations (optional - without country slug)
    path('upload/', views.company_upload, name='company_upload_global'),
    path('upload/result/', views.company_upload_result, name='company_upload_result'),
]