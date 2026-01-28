"""
URL configuration for ExactusPay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from Exactus.accounts.views import tab_close_detection
from django.views.generic import RedirectView

urlpatterns = [

    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home-redirect'),
    path('admin/management/executive/panel/', admin.site.urls),

    path('',include('Exactus.accounts.urls')),
    path('',include('Exactus.country.urls')),
    path('',include('Exactus.company.urls')),
    path('',include('Exactus.regulations.urls')),
    path('',include('Exactus.elements.urls')),
    path('',include('Exactus.calculationbase.urls')),
    path('',include('Exactus.employee.urls')),
    path('',include('Exactus.pdcodes.urls')),
    path('',include('Exactus.payroll.urls')),
    path('',include("Exactus.compensation.urls")),
    path('',include("Exactus.reports.urls")),
    

    path('ajax/tab-close/', tab_close_detection, name='tab_close'),
    
]
