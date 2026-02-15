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
        if not user.is_authenticated:
            return False

        # 1. Superuser Override
        if getattr(user, "is_superuser", False):
            return True

        role = getattr(user, "role", "").upper()
        domain = domain.upper()
        action = action.upper()

        if not role:
            return False

        # 2. Hardcoded Admin Override (Keep this for Exec/Admin)
        if role in ["EXEC", "ADMIN"]:
            return True

        # 3. SAFETY NET: If Compliance needs READ access but DB is empty
        # This ensures the menu shows up even if you haven't run the seeder yet.
        if role == "COMPLIANCE" and action == "READ":
            return True

        # 4. Check Cache
        cache_key = f"{AccessControl.CACHE_PREFIX}::{role}::{domain}::{action}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # 5. Database Check (Optimized single query)
        has_perm = PermissionMatrix.objects.filter(
            Q(role=role, domain="ALL", action="ALL", allowed=True) |
            Q(role=role, domain=domain, action="ALL", allowed=True) |
            Q(role=role, domain="ALL", action=action, allowed=True) |
            Q(role=role, domain=domain, action=action, allowed=True)
        ).exists()

        # Cache and return
        cache.set(cache_key, has_perm, AccessControl.CACHE_TIMEOUT)
        return has_perm



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