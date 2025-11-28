from django.core.cache import cache
from django.db.models import Q

from Exactus.accounts.models import PermissionMatrix


class AccessControl:
    """
    Production-ready permission engine with SAFE wildcard expansion.
    Evaluation order prevents privilege escalation while maintaining flexibility.
    """

    CACHE_TIMEOUT = 60 * 5  # 5 minutes
    CACHE_PREFIX = "perm"

    @staticmethod
    def has_permission(user, domain, action):
        """
        Secure permission check with caching and proper evaluation order.
        """
        # 1. Authentication check
        if not getattr(user, "is_authenticated", False):
            return False

        # 2. Superuser override
        if getattr(user, "is_superuser", False):
            return True

        role = getattr(user, "role", None)
        if not role:
            return False

        role = role.upper()
        domain = domain.upper()
        action = action.upper()

        # 3. EXEC/ADMIN role override
        if role in ["EXEC", "ADMIN"]:
            return True

        # 4. Cache lookup
        cache_key = f"{AccessControl.CACHE_PREFIX}::{role}::{domain}::{action}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result

        # 5. SAFE EVALUATION ORDER (prevents escalation)
        result = False
        
        # Check in order of specificity
        checks = [
            # Global super-permission
            Q(role=role, domain="ALL", action="ALL", allowed=True),
            # Domain-wide permission  
            Q(role=role, domain=domain, action="ALL", allowed=True),
            # Action-wide permission
            Q(role=role, domain="ALL", action=action, allowed=True),
            # Specific permission
            Q(role=role, domain=domain, action=action, allowed=True)
        ]
        
        for check in checks:
            if PermissionMatrix.objects.filter(check).exists():
                result = True
                break

        # Cache the result
        cache.set(cache_key, result, AccessControl.CACHE_TIMEOUT)
        return result

    @staticmethod
    def purge_user_cache(user=None):
        """
        Efficient cache clearing - clear specific user or all permissions
        """
        if user and hasattr(user, 'role'):
            # Clear only this user's permissions
            pattern = f"{AccessControl.CACHE_PREFIX}::{user.role.upper()}::*"
            cache.delete_pattern(pattern)
        else:
            # Clear all permission cache
            cache.delete_pattern(f"{AccessControl.CACHE_PREFIX}::*")

    @staticmethod
    def get_effective_permissions(role):
        """
        Get all expanded permissions for a role (for UI display)
        """
        role = role.upper()
        permissions = PermissionMatrix.objects.filter(role=role, allowed=True)
        
        effective_perms = set()
        
        for perm in permissions:
            if perm.domain == "ALL" and perm.action == "ALL":
                # Global super-permission - add everything
                for domain_code, _ in PermissionMatrix.DOMAIN_CHOICES:
                    for action_code, _ in PermissionMatrix.ACTION_CHOICES:
                        effective_perms.add(f"{domain_code}:{action_code}")
            elif perm.domain == "ALL":
                # Action-wide - add to all domains
                for domain_code, _ in PermissionMatrix.DOMAIN_CHOICES:
                    effective_perms.add(f"{domain_code}:{perm.action}")
            elif perm.action == "ALL":
                # Domain-wide - add all actions for this domain
                for action_code, _ in PermissionMatrix.ACTION_CHOICES:
                    effective_perms.add(f"{perm.domain}:{action_code}")
            else:
                # Specific permission
                effective_perms.add(f"{perm.domain}:{perm.action}")
                
        return sorted(effective_perms)

    @staticmethod
    def bulk_has_permission(user, permission_list):
        """
        Check multiple permissions efficiently in one call
        Usage: bulk_has_permission(user, [("USER", "READ"), ("PAYROLL", "WRITE")])
        """
        return all(AccessControl.has_permission(user, domain, action) 
                   for domain, action in permission_list)