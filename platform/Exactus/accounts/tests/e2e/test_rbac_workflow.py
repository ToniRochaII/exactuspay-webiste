# tests/e2e/test_rbac_workflow.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import PermissionMatrix, Role, Domain

class TestRBACEndToEnd:
    """End-to-end RBAC workflow tests"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        User = get_user_model()
        return User.objects.create_user(
            username='e2e_admin',
            password='password',
            role='ADMIN'
        )
    
    @pytest.fixture
    def manager_user(self):
        User = get_user_model()
        return User.objects.create_user(
            username='e2e_manager', 
            password='password',
            role='MANAGER'
        )
    
    def test_complete_rbac_workflow(self, api_client, admin_user, manager_user):
        """Test complete RBAC workflow from Django to NodeJS"""
        
        # 1. Admin sets up permissions in Django
        api_client.force_authenticate(user=admin_user)
        
        payrun_domain = Domain.objects.get(name='PAYRUN')
        manager_role = Role.objects.get(name='MANAGER')
        
        # Grant MANAGER payrun create permission
        PermissionMatrix.objects.create(
            role=manager_role,
            domain=payrun_domain,
            action='CREATE',
            allowed=True
        )
        
        # 2. Verify effective permissions in Django
        response = api_client.get('/api/permissions/effective/MANAGER/')
        assert response.status_code == 200
        assert response.data['domains']['PAYRUN']['CREATE'] == True
        
        # 3. Simulate NodeJS API call with MANAGER role
        api_client.force_authenticate(user=manager_user)
        
        # This would be called by NodeJS middleware
        validation_response = api_client.post('/api/permissions/validate/', {
            'role': 'MANAGER',
            'domain': 'PAYRUN', 
            'action': 'CREATE'
        })
        
        assert validation_response.status_code == 200
        assert validation_response.data['has_permission'] == True
        
        # 4. Test permission denial scenario
        validation_response = api_client.post('/api/permissions/validate/', {
            'role': 'MANAGER',
            'domain': 'PAYRUN',
            'action': 'DELETE'  # Not granted
        })
        
        assert validation_response.data['has_permission'] == False

# tests/e2e/test_cache_sync.py
class TestCacheSynchronization:
    """Test Redis cache synchronization between Django and NodeJS"""
    
    def test_cache_invalidation_propagation(self):
        """Test that cache invalidation propagates to all services"""
        from accounts.services.permission_resolver import permission_resolver
        
        # Prime the cache
        effective1 = permission_resolver.resolve_permissions()
        
        # Make permission change
        PermissionMatrix.objects.create(
            role=Role.objects.get(name='MANAGER'),
            domain=Domain.objects.get(name='EMPLOYEE'),
            action='READ',
            allowed=True
        )
        
        # Invalidate cache
        permission_resolver.invalidate_cache()
        
        # Resolve again - should reflect changes
        effective2 = permission_resolver.resolve_permissions(force_refresh=True)
        
        # Verify change is visible
        assert effective1['MANAGER'].get('EMPLOYEE', {}).get('READ', False) != \
               effective2['MANAGER']['EMPLOYEE']['READ']
        
        # Verify Redis was updated
        from accounts.services.redis_cache import DistributedPermissionCache
        redis_cache = DistributedPermissionCache()
        redis_perms = redis_cache.get_permissions('MANAGER')
        
        assert redis_perms['EMPLOYEE']['READ'] == True