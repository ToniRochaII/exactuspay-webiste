from django.contrib import admin
from .models import User, UserProfile, PermissionMatrix, RoleTemplate, RoleHierarchy, PermissionBulkUpdate, CustomRole


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "city", "country")
    search_fields = ("user__username", "phone_number", "city", "country")


@admin.register(PermissionMatrix)
class PermissionMatrixAdmin(admin.ModelAdmin):
    list_display = ("role", "domain", "action", "allowed")
    list_filter = ("role", "domain", "action", "allowed")
    search_fields = ("role", "domain", "action")


@admin.register(RoleTemplate)
class RoleTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(RoleHierarchy)
class RoleHierarchyAdmin(admin.ModelAdmin):
    list_display = ("parent", "child")
    list_filter = ("parent",)
    search_fields = ("parent", "child")


@admin.register(PermissionBulkUpdate)
class PermissionBulkUpdateAdmin(admin.ModelAdmin):
    list_display = ('name', 'applied_by', 'applied_at', 'changes_count')
    list_filter = ('applied_at', 'applied_by')
    readonly_fields = ('applied_at',)
    
    def changes_count(self, obj):
        return len(obj.changes.get('updated_count', []))
    changes_count.short_description = 'Changes Count'


@admin.register(CustomRole)
class CustomRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'scope', 'is_active', 'created_by', 'created_at', 'permission_count')
    list_filter = ('scope', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def permission_count(self, obj):
        return obj.get_permission_count()
    permission_count.short_description = 'Permissions'