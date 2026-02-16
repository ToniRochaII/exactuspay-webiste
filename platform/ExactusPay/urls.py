"""
URL configuration for ExactusPay project.
"""
import os
from django.conf import settings
from django.conf.urls.static import static
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
    path('', include('Exactus.regulations.urls')),
    path('', include('Exactus.elements.urls')),
    path('', include('Exactus.calculationbase.urls')),
    path('', include('Exactus.pdcodes.urls')),
    path('', include('Exactus.payroll.urls')),
    path('', include("Exactus.compensation.urls")),
    path('', include("Exactus.reports.urls")),
    path('', include('Exactus.employee.urls')),

    # 3. Company / Country Catch-All
    path('', include('Exactus.company.urls')),
    
    path('', include('Exactus.ess.urls')),

    path('ajax/tab-close/', tab_close_detection, name='tab_close'),
    
]

# ================================
# MEDIA SERVING (FIX FOR RENDER)
# ================================
# This block allows Django to serve user uploads (avatars) from the persistent disk
if settings.DEBUG or 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)