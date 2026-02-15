# tests/fuzzing/test_rbac_fuzzing.py
import random
import string
from django.test import TestCase
from accounts.services.permission_resolver import permission_resolver

class TestRBACFuzzing(TestCase):
    """Fuzzing tests to find edge cases and vulnerabilities"""
    
    def generate_random_string(self, length=10):
        """Generate random strings for fuzzing"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def test_permission_matrix_fuzzing(self):
        """Fuzz test permission matrix with random data"""
        for _ in range(1000):  # 1000 fuzzing iterations
            random_role = self.generate_random_string(8)
            random_domain = self.generate_random_string(8)
            random_action = self.generate_random_string(6)
            
            # Should not crash with random inputs
            try:
                effective = permission_resolver.resolve_permissions()
                
                # Try to access random permission
                if random_role in effective:
                    if random_domain in effective[random_role]:
                        permission = effective[random_role][random_domain].get(random_action, False)
                        
                        # Just verify no exception thrown
                        self.assertIn(permission, [True, False])
                        
            except Exception as e:
                self.fail(f"Fuzzing caused exception: {e}")
    
    def test_api_endpoint_fuzzing(self):
        """Fuzz test API endpoints with malformed data"""
        client = APIClient()
        client.force_authenticate(user=self.admin_user)
        
        malformed_payloads = [
            None,
            "",
            {"invalid": "data"},
            {"role": None, "domain": None, "action": None},
            {"role": "", "domain": "", "action": ""},
            {"role": "A" * 1000, "domain": "B" * 1000, "action": "C" * 1000},
            {"role": "<script>", "domain": "<script>", "action": "<script>"},
            {"role": "MANAGER; DROP TABLE", "domain": "PAYRUN--", "action": "READ"},
        ]
        
        for payload in malformed_payloads:
            response = client.post('/api/permissions/validate/', payload)
            
            # Should not crash with 500 error
            self.assertNotEqual(response.status_code, 500)
            
            # Should either handle gracefully or return 400
            self.assertIn(response.status_code, [200, 400, 403])

# Run fuzzing tests with: python manage.py test tests.fuzzing --verbosity=2