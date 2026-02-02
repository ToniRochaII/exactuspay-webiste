# Exactus/accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from Exactus.accounts import views

urlpatterns = [
    # 1. Profile & Settings
    path('profile/', views.profile, name='profile'),
    
    # 2. Dashboards
    path('dashboard/redirect/', views.role_based_redirect, name='role_based_redirect'),
    path('dashboard/exec/', views.dashboard_exec, name='dashboard_exec'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/general/', views.dashboard, name='dashboard_general'),
    path('dashboard/employee/', views.dashboard, name='dashboard_employee'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # 3. Auth & Registration
    path('register/', views.register, name='register'),
    
    # --- FIX 1: Use custom_login instead of default LoginView ---
    path('login/', views.custom_login, name='login'),
    # ------------------------------------------------------------
    
    path('logout/', views.enhanced_logout, name='enhanced_logout'),

    # 4. Password Management
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # 5. User Management & Admin Tools
    path('export-users/', views.export_users_csv, name='export_users_csv'),
    path('users/', views.user_list, name='user_list'),
    
    # --- FIX 2: Added missing user_detail path ---
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    # ---------------------------------------------
    
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path("users/<int:user_id>/reset-password/", views.admin_reset_password, name="admin_reset_password"),
    path("users/<int:user_id>/resend-welcome/", views.resend_welcome_email, name="resend_welcome_email"),
    path('switch-context/<int:company_id>/', views.switch_context, name='switch_context'),
    
    # 6. Roles
    path('roles/', views.role_management, name='role_management'),
    
    # 7. Utilities (Optional but good for completeness based on views.py)
    path('session-status/', views.session_status, name='session_status'),
    path('heartbeat/', views.heartbeat, name='heartbeat'),
]