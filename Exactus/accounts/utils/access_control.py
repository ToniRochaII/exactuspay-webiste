from django.core.cache import cache
from django.conf import settings

from Exactus.accounts.models import PermissionMatrix


class AccessControl:
    """
    Permission engine with SAFE wildcard expansion.
    Supports:
      - (ALL, ALL)     → global super-permission
      - (domain, ALL)  → domain-wide permission
      - (ALL, action)  → action-wide permission
      - (domain, action) → exact match

    Order of evaluation prevents privilege escalation.
    """

    CACHE_TIMEOUT = 60 * 5  # 5 minutes

    @staticmethod
    def has_permission(user, domain, action):
        """
        Secure permission check with caching.
        """

        # 1. Not authenticated → deny
        if not getattr(user, "is_authenticated", False):
            return False

        # 2. Django superuser → full access
        if getattr(user, "is_superuser", False):
            return True

        role = getattr(user, "role", None)
        if not role:
            return False

        role = role.upper()
        domain = domain.upper()
        action = action.upper()

        # 3. EXEC / ADMIN override
        if role in ["EXEC", "ADMIN"]:
            return True

        # 4. Cache lookup
        cache_key = f"perm::{role}::{domain}::{action}"
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        # 5. Safe wildcard evaluation order

        # (A) Global super-permission: ALL/ALL
        if PermissionMatrix.objects.filter(
            role=role, domain="ALL", action="ALL", allowed=True
        ).exists():
            cache.set(cache_key, True, AccessControl.CACHE_TIMEOUT)
            return True

        # (B) Domain-wide: domain/ALL
        if PermissionMatrix.objects.filter(
            role=role, domain=domain, action="ALL", allowed=True
        ).exists():
            cache.set(cache_key, True, AccessControl.CACHE_TIMEOUT)
            return True

        # (C) Action-wide: ALL/action
        if PermissionMatrix.objects.filter(
            role=role, domain="ALL", action=action, allowed=True
        ).exists():
            cache.set(cache_key, True, AccessControl.CACHE_TIMEOUT)
            return True

        # (D) Exact match: domain/action
        result = PermissionMatrix.objects.filter(
            role=role, domain=domain, action=action, allowed=True
        ).exists()

        cache.set(cache_key, result, AccessControl.CACHE_TIMEOUT)
        return result

    @staticmethod
    def purge_cache():
        """
        Clears permission cache when permissions change.
        """
        cache.clear()

    @staticmethod
    def get_effective_permissions(role):
        """
        Returns all effective permissions (expanded wildcard rules).
        Useful for display, debugging, and admin preview.
        """
        role = role.upper()
        perms = PermissionMatrix.objects.filter(role=role, allowed=True)

        effective = set()

        for p in perms:
            if p.domain == "ALL" and p.action == "ALL":
                # Full matrix
                for d, _ in PermissionMatrix.DOMAIN_CHOICES:
                    for a, _ in PermissionMatrix.ACTION_CHOICES:
                        effective.add((d, a))

            elif p.domain == "ALL":
                # Action-wide
                for d, _ in PermissionMatrix.DOMAIN_CHOICES:
                    effective.add((d, p.action))

            elif p.action == "ALL":
                # Domain-wide
                for a, _ in PermissionMatrix.ACTION_CHOICES:
                    effective.add((p.domain, a))

            else:
                # Exact
                effective.add((p.domain, p.action))

        return effective
