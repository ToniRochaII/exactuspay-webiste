# tests/security/test_rbac_security.py
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.services.permission_resolver import permission_resolver

class TestRBACSecurity(TestCase):
    """Security penetration tests for RBAC system"""
    
    def test_role_escalation_prevention(self):
        """Test that users cannot escalate their roles"""
        client = APIClient()
        
        # Create a regular user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username='attacker',
            password='password',
            role='SPECIALIST'  # Low privilege role
        )
        
        client.force_authenticate(user=user)
        
        # Try to access high-privilege endpoints
        response = client.get('/api/permissions/effective/EXEC/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        # Try to modify permissions
        response = client.post('/api/permissions/validate/', {
            'role': 'EXEC',  # Trying to check EXEC permissions
            'domain': 'USER',
            'action': 'MANAGE'
        })
        # Should only be able to check own role or get denied
        self.assertIn(response.status_code, [200, 403])
    
    def test_injection_attempts(self):
        """Test SQL injection and other injection attempts"""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        # SQL injection in role parameter
        response = client.get('/api/permissions/effective/MANAGER; DROP TABLE users--/')
        self.assertIn(response.status_code, [404, 400])  # Should not crash
        
        # XSS attempts in domain names
        response = client.post('/api/permissions/validate/', {
            'role': 'MANAGER',
            'domain': '<script>alert("xss")</script>',
            'action': 'READ'
        })
        self.assertEqual(response.status_code, 400)  # Should validate input
    
    def test_brute_force_protection(self):
        """Test protection against permission brute forcing"""
        client = APIClient()
        
        # Simulate rapid permission checks
        for i in range(100):
            response = client.post('/api/permissions/validate/', {
                'role': f'ROLE_{i}',
                'domain': 'PAYRUN',
                'action': 'CREATE'
            })
            
            # After many attempts, should not leak information
            if i > 50:
                self.assertNotIn('internal error', response.content.decode().lower())

# tests/security/test_cache_poisoning.py
class TestCacheSecurity(TestCase):
    """Test cache poisoning and tampering attempts"""
    
    def test_redis_cache_tampering(self):
        """Test that tampered Redis cache doesn't break system"""
        from accounts.services.redis_cache import DistributedPermissionCache
        
        redis_cache = DistributedPermissionCache()
        
        # Simulate attacker tampering with Redis
        malicious_data = {
            'domains': {
                'PAYRUN': {
                    'READ': True,
                    'CREATE': True,
                    'DELETE': True,  # Should be denied for most roles
                    'MANAGE': True
                }
            }
        }
        
        # Inject malicious data
        redis_cache.set_permissions('FINANCE', malicious_data)
        
        # System should still enforce business rules
        effective = permission_resolver.resolve_permissions(force_refresh=True)
        
        # Business logic should override tampered data
        self.assertFalse(effective['FINANCE']['PAYRUN']['DELETE'])
        self.assertFalse(effective['FINANCE']['PAYRUN']['CREATE'])