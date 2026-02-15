# tests/performance/test_rbac_performance.py
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from django.test import TestCase
from accounts.services.permission_resolver import permission_resolver

class TestRBACPerformance(TestCase):
    """Performance and load testing for RBAC system"""
    
    def test_concurrent_permission_checks(self):
        """Test performance under concurrent load"""
        def check_permissions(role, domain, action):
            return permission_resolver.resolve_permissions()[role][domain].get(action, False)
        
        # Simulate 100 concurrent permission checks
        roles = ['MANAGER', 'FINANCE', 'DIRECTOR'] * 33
        domains = ['PAYRUN', 'EMPLOYEE', 'COMPANY'] * 33
        actions = ['READ', 'CREATE', 'UPDATE'] * 33
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(check_permissions, role, domain, action)
                for role, domain, action in zip(roles, domains, actions)
            ]
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        
        # Should complete within 2 seconds
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(len(results), 100)
    
    def test_cache_performance(self):
        """Test cache performance benefits"""
        # First call (cold cache)
        start_time = time.time()
        effective1 = permission_resolver.resolve_permissions()
        cold_cache_time = time.time() - start_time
        
        # Second call (warm cache)
        start_time = time.time()
        effective2 = permission_resolver.resolve_permissions()
        warm_cache_time = time.time() - start_time
        
        # Warm cache should be significantly faster
        self.assertLess(warm_cache_time, cold_cache_time)
        self.assertLess(warm_cache_time, 0.1)  # Should be very fast
        
        # Results should be identical
        self.assertEqual(effective1, effective2)

# tests/performance/test_nodejs_performance.js
const loadTest = require('loadtest');
const rbacMiddleware = require('../middleware/rbacMiddleware');

describe('NodeJS RBAC Performance Tests', () => {
    test('should handle 1000 requests per minute', async () => {
        const options = {
            url: 'http://localhost:3000/api/payruns',
            maxRequests: 1000,
            concurrency: 10,
            method: 'GET',
            headers: {
                'Authorization': 'Bearer test-token'
            }
        };

        return new Promise((resolve, reject) => {
            loadTest.loadTest(options, (error, result) => {
                if (error) {
                    reject(error);
                } else {
                    expect(result.totalErrors).toBe(0);
                    expect(result.totalTimeSeconds).toBeLessThan(60);
                    expect(result.rps).toBeGreaterThan(16); // 1000/60
                    resolve();
                }
            });
        });
    });
});