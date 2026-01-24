from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

# ──────────────────────────────────────────────────────────────────────────────
# 1. MAIN USER MODEL
# ──────────────────────────────────────────────────────────────────────────────

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

    # Bulk Access Management (Client Groups)
    client_group = models.ForeignKey(
        'company.ClientGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text=_("Assigning a group gives this user access to ALL companies in that group.")
    )

    # Grouping logic for Access Control
    BUSINESS_ROLES = {
        "EXEC", "ADMIN", "COMPLIANCE", "BILLING", 
        "IMPLEMENTATION", "OPERATION"
    }
    
    CLIENT_ROLES = {
        "DIRECTOR", "MANAGER", "SPECIALIST", 
        "FINANCE", "EMPLOYEE"
    }

    @property
    def access_type(self):
        if self.role in self.BUSINESS_ROLES:
            return "BUSINESS"
        return "CLIENT"

    @property
    def is_business_user(self):
        return self.role in self.BUSINESS_ROLES

    @property
    def is_client_user(self):
        return self.role in self.CLIENT_ROLES

    def get_accessible_companies(self):
        """
        Efficiently returns all companies the user can access, 
        combining direct Group access and specific UserCompany links.
        """
        # 1. Superusers and Business Execs get everything
        if self.is_superuser or self.role in ["EXEC", "ADMIN"]:
            from Exactus.company.models import Company
            return Company.objects.all()

        # 2. Start with companies from their assigned Client Group
        if self.client_group:
            companies = self.client_group.companies.all()
        else:
            from Exactus.company.models import Company
            companies = Company.objects.none()

        # 3. Add individually assigned companies (from UserCompany table)
        # This handles exceptions where a user needs their Group + 1 extra company
        # or if they don't have a group but have specific assignments.
        extra_companies = self.company_access.filter(is_active=True).values_list('company', flat=True)
        
        if extra_companies:
            from Exactus.company.models import Company
            # Union of group companies and specific companies
            companies = companies | Company.objects.filter(id__in=extra_companies)

        return companies.distinct()


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
    notification_frequency = models.CharField(
        max_length=20,
        choices=[('IMMEDIATE', 'Immediately'), ('DAILY', 'Daily Digest'), ('WEEKLY', 'Weekly Digest')],
        default='IMMEDIATE'
    )

    force_password_change = models.BooleanField(default=False, help_text="User redirected to change password on login.")
    two_factor_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def full_name(self):
        return f"{self.name or ''} {self.surname or ''}".strip() or self.user.username


# ──────────────────────────────────────────────────────────────────────────────
# 2. RBAC, AUDIT, NOTIFICATIONS (Standard Models)
# ──────────────────────────────────────────────────────────────────────────────

class PermissionMatrix(models.Model):
    ROLE_CHOICES = User.ROLE_CHOICES
    DOMAIN_CHOICES = [
        ("ALL", "All"), ("RULE", "Regulation"), ("COMPANY", "Company"), ("PAYROLL", "Payroll"),
        ("PERIOD", "Payroll Period"), ("EMPLOYEE", "Employee"), ("REPORT", "Reports"),
        ("USER", "User Management"), ("ROLE", "Role Management"),
        ("COMPANY_USER", "Company User Management"), ("NOTIFICATION", "Notification Management")
    ]
    ACTION_CHOICES = [
        ("ALL", "All"), ("CREATE", "Create"), ("READ", "Read"), ("UPDATE", "Update"),
        ("DELETE", "Delete"), ("EXECUTE", "Execute"), ("TRANSFER", "Transfer"),
        ("APPROVE", "Approve"), ("ASSIGN", "Assign"), ("EXPORT", "Export"), ("IMPORT", "Import")
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    allowed = models.BooleanField(default=True)

    class Meta:
        unique_together = ("role", "domain", "action")
        ordering = ["role", "domain", "action"]
        indexes = [models.Index(fields=['role', 'domain', 'action'])]

    def __str__(self):
        return f"{self.role} → {self.domain} → {self.action}"


class PermissionBulkUpdate(models.Model):
    name = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)
    applied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)


class RoleTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rules = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)


class RoleHierarchy(models.Model):
    parent = models.CharField(max_length=50)
    child = models.CharField(max_length=50)
    class Meta:
        unique_together = ("parent", "child")


class CustomRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.JSONField(default=dict, blank=True)
    scope = models.CharField(max_length=20, default='GLOBAL')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ──────────────────────────────────────────────────────────────────────────────
# 3. USER COMPANY LINK (For exceptions to Group Rule)
# ──────────────────────────────────────────────────────────────────────────────

COMPANY_ROLE_CHOICES = [
    ('OWNER', 'Owner'), ('ADMIN', 'Company Administrator'), ('PAYROLL_MANAGER', 'Payroll Manager'),
    ('HR_MANAGER', 'HR Manager'), ('FINANCE', 'Finance Team'), ('MANAGER', 'Department Manager'),
    ('VIEWER', 'Viewer'), ('EMPLOYEE', 'Employee')
]

class UserCompany(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_access')
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='authorized_users')
    role = models.CharField(max_length=50, choices=COMPANY_ROLE_CHOICES, default='VIEWER')
    permissions = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    access_granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_access')
    access_granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'company']


class UserContextMapping(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    context_key = models.CharField(max_length=100)
    context_value = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('user', 'context_key')


# ──────────────────────────────────────────────────────────────────────────────
# 4. NOTIFICATIONS & AUDIT
# ──────────────────────────────────────────────────────────────────────────────

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # (Simplified for brevity, keep your full fields if needed)
    
    class Meta:
        ordering = ['-created_at']


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
        ("NOTIFICATION_CREATED", "Notification Created"),
        ("NOTIFICATION_READ", "Notification Read"),
        ("COMPANY_ACCESS_GRANTED", "Company Access Granted"),
        ("COMPANY_ACCESS_REVOKED", "Company Access Revoked"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255, blank=True, null=True)
    
    # These were missing or causing issues:
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    
    company = models.ForeignKey(
        'company.Company', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.user} - {self.action}"


# ──────────────────────────────────────────────────────────────────────────────
# 5. HELPERS
# ──────────────────────────────────────────────────────────────────────────────

class UserPermissionHelper:
    @staticmethod
    def can_access_company(user, company):
        if user.is_business_user or user.is_superuser: return True
        return company in user.get_accessible_companies()

    @staticmethod
    def get_user_companies(user):
        return user.get_accessible_companies()