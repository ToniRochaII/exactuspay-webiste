# accounts/services/permission_resolver.py
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class PermissionResolver:
    """Enterprise-grade permission resolution service for ExactusPay"""
    
    CACHE_KEY = "effective_permissions_v2"
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def __init__(self):
        self.payroll_domains = ['PAYRUN', 'PAYREGISTER', 'CALCULATION', 'COMPANY', 'EMPLOYEE', 'PDCODES']
        self.system_domains = ['USER', 'ROLE', 'SYSTEM', 'SECURITY']
        self.protected_roles = ['EXEC', 'ADMIN', 'FINANCE']
    
    def resolve_permissions(self, force_refresh=False):
        """Resolve effective permissions with caching"""
        if not force_refresh:
            cached = cache.get(self.CACHE_KEY)
            if cached:
                logger.debug("Returning cached effective permissions")
                return cached
        
        logger.info("Computing effective permissions (cache miss)")
        with transaction.atomic():
            effective = self._compute_effective_permissions()
            cache.set(self.CACHE_KEY, effective, self.CACHE_TIMEOUT)
            return effective
    
    def _compute_effective_permissions(self):
        """Compute final resolved permissions after all business rules"""
        from accounts.models import PermissionMatrix, RoleHierarchy
        
        # Load all data in single queries for performance
        matrix_data = self._load_permission_matrix()
        hierarchy_data = self._load_role_hierarchy()
        
        effective = {}
        
        for role in matrix_data.keys():
            effective[role] = {}
            
            # 1. Start with explicit permissions
            for domain, actions in matrix_data[role].items():
                effective[role][domain] = actions.copy()
            
            # 2. Apply hierarchy inheritance
            self._apply_hierarchy_inheritance(effective, role, hierarchy_data, matrix_data)
            
            # 3. Apply business logic protections
            self._apply_business_logic_protections(effective[role], role)
        
        return effective
    
    def _load_permission_matrix(self):
        """Load permission matrix efficiently"""
        from accounts.models import PermissionMatrix
        matrix = {}
        
        for pm in PermissionMatrix.objects.select_related('role', 'domain').all():
            role_name = pm.role.name
            domain_name = pm.domain.name
            
            if role_name not in matrix:
                matrix[role_name] = {}
            if domain_name not in matrix[role_name]:
                matrix[role_name][domain_name] = {}
            
            matrix[role_name][domain_name][pm.action] = pm.allowed
        
        return matrix
    
    def _load_role_hierarchy(self):
        """Load role hierarchy relationships"""
        from accounts.models import RoleHierarchy
        hierarchy = {}
        
        for rh in RoleHierarchy.objects.select_related('parent_role', 'child_role').all():
            hierarchy[rh.child_role.name] = rh.parent_role.name
        
        return hierarchy
    
    def _apply_hierarchy_inheritance(self, effective, role, hierarchy, matrix):
        """Apply inheritance from parent roles"""
        parent_role = hierarchy.get(role)
        if parent_role and parent_role in matrix:
            for domain, actions in matrix[parent_role].items():
                if domain not in effective[role]:
                    effective[role][domain] = {}
                for action, allowed in actions.items():
                    if allowed and not effective[role][domain].get(action):
                        effective[role][domain][action] = True
                        # Mark as inherited for audit purposes
                        effective[role][domain][f"{action}_inherited"] = True
    
    def _apply_business_logic_protections(self, permissions, role):
        """Apply ExactusPay-specific business logic rules"""
        if role == 'FINANCE':
            # FINANCE is strictly read-only for payroll operations
            for domain in self.payroll_domains:
                if domain in permissions:
                    for action in ['CREATE', 'DELETE', 'UPDATE']:
                        if permissions[domain].get(action):
                            permissions[domain][action] = False
                            permissions[domain][f"{action}_protected"] = True
        
        elif role in ['EXEC', 'ADMIN']:
            # EXEC/ADMIN must have full system access
            for domain in self.system_domains:
                if domain in permissions:
                    permissions[domain]['MANAGE'] = True
                    permissions[domain]['READ'] = True
    
    def invalidate_cache(self):
        """Invalidate the permissions cache"""
        cache.delete(self.CACHE_KEY)
        logger.info("Permission cache invalidated")

# Singleton instance
permission_resolver = PermissionResolver()