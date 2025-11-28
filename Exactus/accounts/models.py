from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.forms import ValidationError




class User(AbstractUser):
    ROLE_CHOICES = [
        ("EXEC", "Exec"),
        ('ADMIN', 'Admin'),
        ('COMPLIANCE', 'Compliance'),
        ('BILLING', 'Billing'),
        ('IMPLEMENTATION', 'Implementation'),
        ('OPERATION', 'Operation'),
        ('DIRECTOR', 'Director'),
        ('MANAGER', 'Manager'),
        ('SPECIALIST', 'Specialist'),
        ('FINANCE', 'Finance'),
        ('EMPLOYEE', 'Employee'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="EMPLOYEE")

    def __str__(self):
        return f"{self.username} ({self.role})"


class PermissionMatrix(models.Model):
    ROLE_CHOICES = [
        ('EXEC', 'Exec'),
        ('ADMIN', 'Admin'),
        ('COMPLIANCE', 'Compliance'),
        ('BILLING', 'Billing'),
        ('IMPLEMENTATION', 'Implementation'),
        ('OPERATION', 'Operation'),
        ('DIRECTOR', 'Director'),
        ('MANAGER', 'Manager'),
        ('SPECIALIST', 'Specialist'),
        ('FINANCE', 'Finance'),
        ('EMPLOYEE', 'Employee'),
    ]

    DOMAIN_CHOICES = [
        ('ALL', 'All'),
        ('RULE', 'Regulation'),
        ('COMPANY', 'Company'),
        ('PAYROLL', 'Payroll'),
        ('PERIOD', 'Payroll Period'),
        ('EMPLOYEE', 'Employee'),
        ('REPORT', 'Reports'),
        ('USER', 'User Management'),
        ('ROLE', 'Role Management'),
    ]

    ACTION_CHOICES = [
        ('ALL', 'All'),
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('EXECUTE', 'Execute'),
        ('TRANSFER', 'Transfer'),
        ('APPROVE', 'Approve'),
        ('ASSIGN', 'Assign'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    allowed = models.BooleanField(default=True)

    class Meta:
        unique_together = ('role', 'domain', 'action')
        ordering = ['role', 'domain', 'action']
        verbose_name_plural = "Permission Matrices"

    def __str__(self):
        return f"{self.role} → {self.domain} → {self.action} ({'✓' if self.allowed else '✗'})"
    
    @property
    def is_superadmin(self):
        return self.role in ["EXEC", "ADMIN"]
    

class PermissionBulkUpdate(models.Model):
    """Track bulk permission updates for audit"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    changes = models.JSONField(default=dict)
    applied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Bulk update: {self.name}"
    
    class Meta:
        ordering = ["-applied_at"]
    

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    surname = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    notify_by_email = models.BooleanField(default=True)
    notify_by_sms = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"



class RoleTemplate(models.Model):
    """
    Optional convenience: a named template of permissions you can apply to a role.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    rules = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name
    def clean(self):
        if not isinstance(self.rules, list):
            raise ValidationError("Rules must be a list of [domain, action] pairs.")


class RoleHierarchy(models.Model):
    parent = models.CharField(max_length=50)
    child = models.CharField(max_length=50)

    class Meta:
        unique_together = ("parent", "child")
        indexes = [models.Index(fields=["parent", "child"])]

    def __str__(self):
        return f"{self.parent} → {self.child}"


class CustomRole(models.Model):
    """Custom roles created by administrators"""
    SCOPE_CHOICES = [
        ('GLOBAL', 'Global - All Companies'),
        ('COMPANY', 'Company-specific'),
        ('DEPARTMENT', 'Department-specific'),
        ('REGION', 'Region-specific'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='GLOBAL')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Store permissions as JSON for flexibility
    permissions = models.JSONField(default=dict, blank=True, help_text="Stores role permissions in format: {'DOMAIN': ['ACTION1', 'ACTION2']}")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"
    
    def get_permission_count(self):
        count = 0
        for actions in self.permissions.values():
            count += len(actions)
        return count
    
    def has_permission(self, domain, action):
        """Check if this custom role has a specific permission"""
        domain_perms = self.permissions.get(domain, [])
        return 'ALL' in domain_perms or action in domain_perms
    
    def add_permission(self, domain, action):
        """Add a permission to this custom role"""
        if domain not in self.permissions:
            self.permissions[domain] = []
        
        if action not in self.permissions[domain]:
            self.permissions[domain].append(action)
        self.save(update_fields=["permissions"])

    @property
    def permission_summary(self):
        return ", ".join(f"{d}: {', '.join(a)}" for d, a in self.permissions.items())
    
    def remove_permission(self, domain, action):
        """Remove a permission from this custom role"""
        if domain in self.permissions and action in self.permissions[domain]:
            self.permissions[domain].remove(action)
            # Clean up empty domains
            if not self.permissions[domain]:
                del self.permissions[domain]


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("LOGIN", "User Login"),
        ("LOGOUT", "User Logout"),
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("VIEW", "View"),
        ("EXPORT", "Export"),
        ("PERMISSION_CHANGE", "Permission Change"),
        ("SECURITY_EVENT", "Security Event"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.user} - {self.action}"


class PermissionMatrix(models.Model):
    # ... existing fields ...
    
    class Meta:
        unique_together = ('role', 'domain', 'action')
        ordering = ['role', 'domain', 'action']
        verbose_name_plural = "Permission Matrices"
        indexes = [
            models.Index(fields=['role', 'domain', 'action', 'allowed']),
            models.Index(fields=['role', 'allowed']),
            models.Index(fields=['domain', 'action']),
        ]