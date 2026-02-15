# accounts/services/audit_logger.py
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
import json

class PermissionAuditLogger:
    """Comprehensive audit logging for permission changes"""
    
    @staticmethod
    def log_permission_change(user, role, domain, action, old_value, new_value, reason=None):
        """Log a permission change with full context"""
        from accounts.models import PermissionChangeLog
        
        change = PermissionChangeLog.objects.create(
            changed_by=user,
            role=role,
            domain=domain,
            action=action,
            old_value=old_value,
            new_value=new_value,
            change_reason=reason,
            ip_address=PermissionAuditLogger._get_client_ip(user),
            user_agent=PermissionAuditLogger._get_user_agent(user),
            effective_permissions_snapshot=PermissionAuditLogger._get_permissions_snapshot(role)
        )
        
        # Also log to Django admin log for compatibility
        PermissionAuditLogger._log_to_admin(user, change)
        
        # Invalidate cache since permissions changed
        from .permission_resolver import permission_resolver
        permission_resolver.invalidate_cache()
        
        return change
    
    @staticmethod
    def log_template_application(user, role, template, effective_changes):
        """Log template application with all changes"""
        from accounts.models import PermissionChangeLog
        
        change = PermissionChangeLog.objects.create(
            changed_by=user,
            role=role,
            domain='SYSTEM',
            action='TEMPLATE_APPLY',
            old_value=None,
            new_value=template.name,
            change_reason=f"Applied template: {template.name}",
            effective_changes=json.dumps(effective_changes),
            is_bulk_operation=True
        )
        
        return change
    
    @staticmethod
    def get_recent_changes(limit=100):
        """Get recent permission changes for audit trail"""
        from accounts.models import PermissionChangeLog
        
        return PermissionChangeLog.objects.select_related('changed_by').order_by('-changed_at')[:limit]