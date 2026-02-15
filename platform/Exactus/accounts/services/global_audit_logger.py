# accounts/services/global_audit_logger.py
class GlobalRBACAuditLogger:
    """Comprehensive audit logging for cross-service RBAC events"""
    
    @staticmethod
    def log_api_permission_check(user, role, domain, action, granted, client_ip, user_agent):
        """Log API permission checks from NodeJS"""
        from accounts.models import GlobalAuditLog
        
        log = GlobalAuditLog.objects.create(
            event_type='API_PERMISSION_CHECK',
            user=user,
            role=role,
            domain=domain,
            action=action,
            result='GRANTED' if granted else 'DENIED',
            client_ip=client_ip,
            user_agent=user_agent,
            service='NodeJS-API',
            metadata={
                'timestamp': timezone.now().isoformat(),
                'endpoint': 'RBAC_MIDDLEWARE'
            }
        )
        return log
    
    @staticmethod
    def log_permission_denial(user, role, domain, action, client_ip, user_agent):
        """Log permission denials for security monitoring"""
        from accounts.models import GlobalAuditLog
        
        log = GlobalAuditLog.objects.create(
            event_type='PERMISSION_DENIAL',
            user=user,
            role=role,
            domain=domain,
            action=action,
            result='DENIED',
            client_ip=client_ip,
            user_agent=user_agent,
            service='NodeJS-API',
            severity='HIGH',
            metadata={
                'security_event': True,
                'investigation_required': True
            }
        )
        
        # Trigger security alert for repeated denials
        GlobalRBACAuditLogger._check_security_alert(user, domain, action)
        return log
    
    @staticmethod
    def log_cache_hit(role, domain, action, cache_source):
        """Log cache performance for optimization"""
        from accounts.models import GlobalAuditLog
        
        GlobalAuditLog.objects.create(
            event_type='CACHE_HIT',
            role=role,
            domain=domain,
            action=action,
            result='HIT',
            service='RBAC_CACHE',
            metadata={
                'cache_source': cache_source,
                'performance_optimized': True
            }
        )