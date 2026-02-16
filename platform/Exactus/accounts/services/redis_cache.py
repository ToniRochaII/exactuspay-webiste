# accounts/services/redis_cache.py
import redis
import json
import pickle
from django.conf import settings
from django.core.cache import cache as django_cache

class DistributedPermissionCache:
    """Redis-powered distributed cache for cross-service permission sync"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_PERMISSION_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.cache_prefix = "exactuspay:permissions:v2"
    
    def set_permissions(self, role, permissions_data, timeout=300):
        """Cache permissions for a specific role"""
        key = f"{self.cache_prefix}:role:{role}"
        self.redis_client.setex(
            key, 
            timeout, 
            json.dumps(permissions_data, default=str)
        )
        
        # Also update the role list for bulk operations
        self._update_role_index(role)
    
    def get_permissions(self, role):
        """Get cached permissions for a role"""
        key = f"{self.cache_prefix}:role:{role}"
        cached = self.redis_client.get(key)
        return json.loads(cached) if cached else None
    
    def get_all_permissions(self):
        """Get all cached permissions (bulk operation)"""
        role_keys = self.redis_client.smembers(f"{self.cache_prefix}:roles")
        permissions = {}
        
        for role_key in role_keys:
            role = role_key.split(":")[-1]
            permissions[role] = self.get_permissions(role)
        
        return permissions
    
    def invalidate_role(self, role):
        """Invalidate cache for a specific role"""
        key = f"{self.cache_prefix}:role:{role}"
        self.redis_client.delete(key)
        self.redis_client.srem(f"{self.cache_prefix}:roles", role)
    
    def invalidate_all(self):
        """Invalidate all permission caches"""
        role_keys = self.redis_client.smembers(f"{self.cache_prefix}:roles")
        for role_key in role_keys:
            self.redis_client.delete(f"{self.cache_prefix}:role:{role_key}")
        self.redis_client.delete(f"{self.cache_prefix}:roles")
    
    def _update_role_index(self, role):
        """Update the role index for bulk operations"""
        self.redis_client.sadd(f"{self.cache_prefix}:roles", role)

# Update the PermissionResolver to use distributed cache
class DistributedPermissionResolver(PermissionResolver):
    """Enhanced resolver with distributed Redis cache"""
    
    def __init__(self):
        super().__init__()
        self.redis_cache = DistributedPermissionCache()
    
    def resolve_permissions(self, force_refresh=False):
        if not force_refresh:
            # Try Redis cache first
            redis_permissions = self.redis_cache.get_all_permissions()
            if redis_permissions and all(redis_permissions.values()):
                logger.debug("Returning Redis cached permissions")
                return redis_permissions
            
            # Fall back to Django cache
            cached = django_cache.get(self.CACHE_KEY)
            if cached:
                # Populate Redis cache from Django cache
                for role, perms in cached.items():
                    self.redis_cache.set_permissions(role, perms)
                return cached
        
        # Compute fresh permissions
        effective = self._compute_effective_permissions()
        
        # Cache in both systems
        django_cache.set(self.CACHE_KEY, effective, self.CACHE_TIMEOUT)
        for role, perms in effective.items():
            self.redis_cache.set_permissions(role, perms)
        
        # Update cache timestamp
        cache_timestamp = timezone.now().isoformat()
        django_cache.set("permissions_cache_timestamp", cache_timestamp)
        self.redis_cache.redis_client.set(
            f"{self.redis_cache.cache_prefix}:timestamp",
            cache_timestamp
        )
        
        return effective
    
    def invalidate_cache(self):
        """Invalidate both Django and Redis caches"""
        super().invalidate_cache()
        self.redis_cache.invalidate_all()