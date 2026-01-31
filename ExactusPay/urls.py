"""
URL configuration for ExactusPay project.
"""
from django.contrib import admin
from django.urls import path, include
from Exactus.accounts.views import tab_close_detection
from django.views.generic import RedirectView

urlpatterns = [

    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home-redirect'),
    path('admin/management/executive/panel/', admin.site.urls),

    # 1. Core Accounts & Country Management
    path('', include('Exactus.accounts.urls')),
    path('', include('Exactus.country.urls')),

    # 2. Specific Modules (Global & Feature Routes)
    # These MUST come before 'company' because they define specific words 
    # (e.g., 'elements/', 'regulations/') that would otherwise be caught 
    # by the company app's generic <slug:country_slug> pattern.
    path('', include('Exactus.regulations.urls')),
    path('', include('Exactus.elements.urls')),
    path('', include('Exactus.calculationbase.urls')),
    path('', include('Exactus.pdcodes.urls')),
    path('', include('Exactus.payroll.urls')),
    path('', include("Exactus.compensation.urls")),
    path('', include("Exactus.reports.urls")),
    path('', include('Exactus.employee.urls')),

    # 3. Company / Country Catch-All
    # This contains <slug:country_slug>/ patterns. It must be LAST.
    path('', include('Exactus.company.urls')),
    

    path('ajax/tab-close/', tab_close_detection, name='tab_close'),
    
]