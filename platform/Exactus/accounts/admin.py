from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, UserProfile, PermissionMatrix, 
    RoleTemplate, CustomRole, UserCompany, 
    Notification, AuditLog, PermissionBulkUpdate
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'client_group', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'client_group')
    fieldsets = UserAdmin.fieldsets + (
        ('Platform Access', {'fields': ('role', 'client_group')}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'country', 'force_password_change')
    search_fields = ('user__username', 'user__email', 'phone_number')

@admin.register(PermissionMatrix)
class PermissionMatrixAdmin(admin.ModelAdmin):
    list_display = ('role', 'domain', 'action', 'allowed')
    list_filter = ('role', 'domain', 'allowed')
    search_fields = ('role', 'domain')

@admin.register(CustomRole)
class CustomRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'scope', 'is_active', 'created_by')
    list_filter = ('scope', 'is_active')
    # We remove 'updated_at' from readonly_fields if it's causing issues, 
    # but based on the model it should be there. 
    # If this fails, your models.py is missing the updated_at field.
    readonly_fields = ('created_at', 'updated_at') 

@admin.register(RoleTemplate)
class RoleTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(UserCompany)
class UserCompanyAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'company__trade_name')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'company', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'target', 'details')
    readonly_fields = ('created_at', 'user', 'action', 'target', 'details', 'ip_address', 'user_agent', 'company')

    def has_add_permission(self, request):
        return False