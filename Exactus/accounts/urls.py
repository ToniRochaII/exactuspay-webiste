from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from Exactus.accounts import views

urlpatterns = [
    # existing routes


    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name="accounts/login.html",redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),

    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'),name='password_reset_confirm'),
    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'),name='password_reset_complete'),
    path("users/<int:user_id>/reset-password/", views.admin_reset_password, name="admin_reset_password"),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    path('profile/', views.profile, name='profile'),

    path('users/', views.user_list, name='user_list'),
    path('users/export/', views.export_users_csv, name='export_users_csv'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),

    path('roles/', views.role_management, name='role_management'),

    path('register/', views.register, name='register'),
    path('users/<int:user_id>/unified/', views.unified_profile, name='unified_profile_view'),


    # Session management
    path('ajax/heartbeat/', views.heartbeat, name='heartbeat'),
    path('ajax/tab-close/', views.tab_close_detection, name='tab_close'),
    path('ajax/session-status/', views.session_status, name='session_status'),
    
    # Optional: Enhanced logout
    path('logout/', views.enhanced_logout, name='logout'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)