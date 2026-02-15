# accounts/tests/test_permission_resolver.py
import pytest
from django.test import TestCase
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from ..services.permission_resolver import PermissionResolver, permission_resolver
from ..models import PermissionMatrix, Role, Domain, RoleHierarchy

class TestPermissionResolver(TestCase):
    
    def setUp(self):
        self.resolver = PermissionResolver()
        cache.clear()
        
        # Create test data
        self.exec_role = Role.objects.create(name='EXEC')
        self.manager_role = Role.objects.create(name='MANAGER')
        self.finance_role = Role.objects.create(name='FINANCE')
        
        self.payrun_domain = Domain.objects.create(name='PAYRUN')
        self.employee_domain = Domain.objects.create(name='EMPLOYEE')
        self.user_domain = Domain.objects.create(name='USER')
        
        # Create hierarchy
        RoleHierarchy.objects.create(
            parent_role=self.exec_role,
            child_role=self.manager_role
        )
    
    def test_basic_permission_resolution(self):
        """Test basic permission resolution without inheritance"""
        # Setup explicit permissions
        PermissionMatrix.objects.create(
            role=self.manager_role,
            domain=self.payrun_domain,
            action='READ',
            allowed=True
        )
        
        effective = self.resolver.resolve_permissions()
        
        self.assertTrue(effective['MANAGER']['PAYRUN']['READ'])
        self.assertFalse(effective['MANAGER']['PAYRUN'].get('CREATE', False))
    
    def test_hierarchy_inheritance(self):
        """Test permission inheritance through role hierarchy"""
        # Parent has CREATE permission
        PermissionMatrix.objects.create(
            role=self.exec_role,
            domain=self.payrun_domain,
            action='CREATE',
            allowed=True
        )
        
        effective = self.resolver.resolve_permissions()
        
        # Manager should inherit CREATE from EXEC
        self.assertTrue(effective['MANAGER']['PAYRUN']['CREATE'])
        self.assertTrue(effective['MANAGER']['PAYRUN'].get('CREATE_inherited', False))
    
    def test_finance_read_only_protection(self):
        """Test FINANCE role read-only enforcement"""
        # Try to give FINANCE CREATE permission
        PermissionMatrix.objects.create(
            role=self.finance_role,
            domain=self.payrun_domain,
            action='CREATE',
            allowed=True
        )
        
        effective = self.resolver.resolve_permissions()
        
        # Business logic should override and deny CREATE
        self.assertFalse(effective['FINANCE']['PAYRUN']['CREATE'])
        self.assertTrue(effective['FINANCE']['PAYRUN'].get('CREATE_protected', False))
    
    def test_exec_system_access_guarantee(self):
        """Test EXEC role always has system access"""
        effective = self.resolver.resolve_permissions()
        
        # EXEC should always have USER management
        self.assertTrue(effective['EXEC']['USER']['MANAGE'])
        self.assertTrue(effective['EXEC']['USER']['READ'])
    
    def test_cache_invalidation(self):
        """Test cache invalidation on permission changes"""
        # First resolution
        effective1 = self.resolver.resolve_permissions()
        
        # Add new permission
        PermissionMatrix.objects.create(
            role=self.manager_role,
            domain=self.employee_domain,
            action='READ',
            allowed=True
        )
        
        # Invalidate cache
        self.resolver.invalidate_cache()
        
        # Second resolution should reflect changes
        effective2 = self.resolver.resolve_permissions(force_refresh=True)
        
        self.assertFalse(effective1['MANAGER']['EMPLOYEE'].get('READ', False))
        self.assertTrue(effective2['MANAGER']['EMPLOYEE']['READ'])
    
    def test_circular_hierarchy_prevention(self):
        """Test prevention of circular role hierarchies"""
        # Try to create circular reference
        RoleHierarchy.objects.create(
            parent_role=self.manager_role,
            child_role=self.exec_role
        )
        
        # Should handle gracefully without infinite recursion
        effective = self.resolver.resolve_permissions()
        
        self.assertIsNotNone(effective)
        self.assertIn('EXEC', effective)
        self.assertIn('MANAGER', effective)

# accounts/tests/test_conflict_detector.py
class TestConflictDetector(TestCase):
    
    def setUp(self):
        self.resolver = PermissionResolver()
        self.effective_permissions = self.resolver.resolve_permissions()
        self.detector = PermissionConflictDetector(self.effective_permissions)
    
    def test_finance_write_access_detection(self):
        """Detect when FINANCE has write access to payroll domains"""
        # Simulate FINANCE having CREATE access (violation)
        self.effective_permissions['FINANCE']['PAYRUN'] = {
            'READ': True,
            'CREATE': True,  # Violation!
            'UPDATE': False,
            'DELETE': False
        }
        
        conflicts = self.detector.detect_conflicts()
        
        finance_violations = [c for c in conflicts if 'FINANCE' in c and 'violates' in c]
        self.assertTrue(len(finance_violations) > 0)
    
    def test_operational_risk_detection(self):
        """Detect operational risks like MANAGER without payrun access"""
        # Simulate MANAGER missing critical permissions
        self.effective_permissions['MANAGER']['PAYRUN'] = {
            'READ': False,  # Manager can't view payruns - operational risk!
            'CREATE': False,
            'UPDATE': False,
            'DELETE': False
        }
        
        risks = self.detector.detect_operational_risks()
        
        manager_risks = [r for r in risks if 'MANAGER' in r and 'cannot' in r]
        self.assertTrue(len(manager_risks) > 0)

# accounts/tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status

class TestPermissionAPI(APITestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin', 
            password='password', 
            role='ADMIN'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_effective_permissions_api(self):
        """Test effective permissions API endpoint"""
        response = self.client.get('/api/permissions/effective/MANAGER/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('role', response.data)
        self.assertIn('domains', response.data)
        self.assertEqual(response.data['role'], 'MANAGER')
    
    def test_permission_validation_api(self):
        """Test permission validation API"""
        data = {
            'role': 'MANAGER',
            'domain': 'PAYRUN',
            'action': 'READ'
        }
        
        response = self.client.post('/api/permissions/validate/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('has_permission', response.data)
        self.assertIn('effective', response.data)
    
    def test_api_authentication_required(self):
        """Test API requires authentication"""
        self.client.logout()
        
        response = self.client.get('/api/permissions/effective/MANAGER/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Run with: python manage.py test accounts.tests