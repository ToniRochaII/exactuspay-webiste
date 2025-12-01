# accounts/models.py (updated)
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


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
    
    # Add fields for multi-tenant support
    is_global_admin = models.BooleanField(default=False, 
                                         help_text="Has access to all companies regardless of UserCompany assignments")
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_executive(self):
        return self.role in ["EXEC", "ADMIN", "DIRECTOR"]
    
    @property
    def is_platform_admin(self):
        return self.role in ["EXEC", "ADMIN"]
    
    def get_companies(self):
        """Get all companies this user can access"""
        from django.db.models import Q
        from Exactus.company.models import Company
        
        if self.is_global_admin:
            return Company.objects.all()
        
        return Company.objects.filter(
            Q(authorized_users__user=self, authorized_users__is_active=True) |
            Q(created_by=self)
        ).distinct()


class PermissionMatrix(models.Model):
    ROLE_CHOICES = [
        ("EXEC", "Exec"),
        ("ADMIN", "Admin"),
        ("COMPLIANCE", "Compliance"),
        ("BILLING", "Billing"),
        ("IMPLEMENTATION", "Implementation"),
        ("OPERATION", "Operation"),
        ("DIRECTOR", "Director"),
        ("MANAGER", "Manager"),
        ("SPECIALIST", "Specialist"),
        ("FINANCE", "Finance"),
        ("EMPLOYEE", "Employee"),
    ]

    DOMAIN_CHOICES = [
        ("ALL", "All"),
        ("RULE", "Regulation"),
        ("COMPANY", "Company"),
        ("PAYROLL", "Payroll"),
        ("PERIOD", "Payroll Period"),
        ("EMPLOYEE", "Employee"),
        ("REPORT", "Reports"),
        ("USER", "User Management"),
        ("ROLE", "Role Management"),
        ("COMPANY_USER", "Company User Management"),  # Added
        ("NOTIFICATION", "Notification Management"),  # Added
    ]

    ACTION_CHOICES = [
        ("ALL", "All"),
        ("CREATE", "Create"),
        ("READ", "Read"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("EXECUTE", "Execute"),
        ("TRANSFER", "Transfer"),
        ("APPROVE", "Approve"),
        ("ASSIGN", "Assign"),
        ("EXPORT", "Export"),
        ("IMPORT", "Import"),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    allowed = models.BooleanField(default=True)

    class Meta:
        unique_together = ("role", "domain", "action")
        ordering = ["role", "domain", "action"]
        verbose_name_plural = "Permission Matrices"
        indexes = [
            models.Index(fields=['role', 'domain', 'action']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        status = "✓" if self.allowed else "✗"
        return f"{self.role} → {self.domain} → {self.action} ({status})"

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
    
    # Preferences
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIATE', 'Immediately'),
            ('DAILY', 'Daily Digest'),
            ('WEEKLY', 'Weekly Digest'),
        ],
        default='IMMEDIATE'
    )
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def full_name(self):
        return f"{self.name or ''} {self.surname or ''}".strip() or self.user.username


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
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['child']),
        ]

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
        indexes = [
            models.Index(fields=['scope', 'is_active']),
        ]
    
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


# Constants for company roles and notifications
COMPANY_ROLE_CHOICES = [
    ('OWNER', 'Owner'),
    ('ADMIN', 'Company Administrator'),
    ('PAYROLL_MANAGER', 'Payroll Manager'),
    ('HR_MANAGER', 'HR Manager'),
    ('FINANCE', 'Finance Team'),
    ('MANAGER', 'Department Manager'),
    ('VIEWER', 'Viewer'),
    ('EMPLOYEE', 'Employee (Self-Service)'),
]

COMPANY_ROLE_DETAILS = {
    'OWNER': {
        'name': 'Owner',
        'description': 'Full company access, can manage users, view all data',
        'permissions': [
            'manage_users', 'manage_payroll', 'view_financials', 
            'export_data', 'configure_settings', 'delete_company'
        ]
    },
    'ADMIN': {
        'name': 'Company Administrator',
        'description': 'Full administrative access except ownership functions',
        'permissions': [
            'manage_users', 'manage_payroll', 'view_financials',
            'export_data', 'configure_settings'
        ]
    },
    'PAYROLL_MANAGER': {
        'name': 'Payroll Manager',
        'description': 'Process payroll, manage payslips, view payroll reports',
        'permissions': [
            'process_payroll', 'manage_payslips', 'view_payroll_reports',
            'export_payroll_data', 'manage_employee_compensation'
        ]
    },
    'HR_MANAGER': {
        'name': 'HR Manager',
        'description': 'Manage employees, contracts, onboarding',
        'permissions': [
            'manage_employees', 'manage_contracts', 'onboard_employees',
            'view_employee_data', 'export_employee_data'
        ]
    },
    'FINANCE': {
        'name': 'Finance Team',
        'description': 'View financial reports, export data',
        'permissions': [
            'view_financial_reports', 'export_financial_data',
            'view_payroll_summary', 'view_tax_reports'
        ]
    },
    'MANAGER': {
        'name': 'Department Manager',
        'description': 'View team members, approve time off',
        'permissions': [
            'view_team_members', 'approve_time_off',
            'view_department_payroll', 'submit_payroll_changes'
        ]
    },
    'VIEWER': {
        'name': 'Viewer',
        'description': 'Read-only access to company data',
        'permissions': [
            'view_company_data', 'view_reports', 'export_own_data'
        ]
    },
    'EMPLOYEE': {
        'name': 'Employee',
        'description': 'Self-service access to own data',
        'permissions': [
            'view_own_payslips', 'update_personal_info',
            'view_own_tax_docs', 'request_time_off'
        ]
    },
}

NOTIFICATION_TYPES = [
    ('SYSTEM', 'System Notification'),
    ('PAYROLL', 'Payroll Update'),
    ('APPROVAL', 'Approval Required'),
    ('DEADLINE', 'Deadline Reminder'),
    ('EMPLOYEE', 'Employee Action'),
    ('COMPLIANCE', 'Compliance Alert'),
    ('SECURITY', 'Security Alert'),
    ('BILLING', 'Billing Update'),
    ('SUPPORT', 'Support Response'),
]

NOTIFICATION_TYPE_DETAILS = {
    'SYSTEM': {
        'name': 'System',
        'icon': 'fas fa-cog',
        'color': 'text-secondary',
        'bg_color': 'bg-secondary-subtle',
        'description': 'Platform updates, maintenance, system changes'
    },
    'PAYROLL': {
        'name': 'Payroll',
        'icon': 'fas fa-file-invoice-dollar',
        'color': 'text-primary',
        'bg_color': 'bg-primary-subtle',
        'description': 'Payroll processing, payslip generation, payroll updates'
    },
    'APPROVAL': {
        'name': 'Approval',
        'icon': 'fas fa-check-circle',
        'color': 'text-warning',
        'bg_color': 'bg-warning-subtle',
        'description': 'Actions requiring your approval or review'
    },
    'DEADLINE': {
        'name': 'Deadline',
        'icon': 'fas fa-clock',
        'color': 'text-danger',
        'bg_color': 'bg-danger-subtle',
        'description': 'Upcoming deadlines and due dates'
    },
    'EMPLOYEE': {
        'name': 'Employee',
        'icon': 'fas fa-user',
        'color': 'text-info',
        'bg_color': 'bg-info-subtle',
        'description': 'Employee actions, requests, updates'
    },
    'COMPLIANCE': {
        'name': 'Compliance',
        'icon': 'fas fa-gavel',
        'color': 'text-purple',
        'bg_color': 'bg-purple-subtle',
        'description': 'Compliance alerts, regulatory updates'
    },
    'SECURITY': {
        'name': 'Security',
        'icon': 'fas fa-shield-alt',
        'color': 'text-success',
        'bg_color': 'bg-success-subtle',
        'description': 'Security alerts, login attempts, access changes'
    },
    'BILLING': {
        'name': 'Billing',
        'icon': 'fas fa-credit-card',
        'color': 'text-indigo',
        'bg_color': 'bg-indigo-subtle',
        'description': 'Billing updates, invoices, payment reminders'
    },
    'SUPPORT': {
        'name': 'Support',
        'icon': 'fas fa-headset',
        'color': 'text-teal',
        'bg_color': 'bg-teal-subtle',
        'description': 'Support responses, ticket updates'
    },
}

NOTIFICATION_PRIORITY = [
    ('CRITICAL', 'Critical'),
    ('HIGH', 'High'),
    ('MEDIUM', 'Medium'),
    ('LOW', 'Low'),
    ('INFO', 'Informational'),
]


class UserCompany(models.Model):
    """Link users to companies they can access (Multi-tenant)"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='company_access'
    )
    
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        related_name='authorized_users'
    )
    
    role = models.CharField(
        max_length=50,
        choices=COMPANY_ROLE_CHOICES,
        default='VIEWER'
    )
    
    # Additional permissions for fine-grained control
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional permissions specific to this user-company relationship"
    )
    
    # Access control
    is_active = models.BooleanField(default=True)
    access_granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_access'
    )
    
    # Dates
    access_granted_at = models.DateTimeField(auto_now_add=True)
    access_revoked_at = models.DateTimeField(null=True, blank=True)
    last_access_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'accounts_user_company'
        verbose_name = 'User Company Access'
        verbose_name_plural = 'User Company Access'
        unique_together = ['user', 'company']
        indexes = [
            models.Index(fields=['user', 'company']),
            models.Index(fields=['company', 'role']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} -> {self.company.trade_name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Update last_access_at if is_active is changing
        if self.pk:
            old_instance = UserCompany.objects.get(pk=self.pk)
            if not old_instance.is_active and self.is_active:
                self.last_access_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def has_full_access(self):
        return self.role in ['OWNER', 'ADMIN']
    
    @property
    def can_access_payroll(self):
        return self.role in ['OWNER', 'ADMIN', 'PAYROLL_MANAGER', 'HR_MANAGER', 'FINANCE']
    
    @property
    def can_manage_users(self):
        return self.role in ['OWNER', 'ADMIN']
    
    def has_company_permission(self, permission_type):
        """Check if user has a specific permission in this company"""
        if permission_type in self.permissions:
            return self.permissions[permission_type]
        
        # Fallback to role-based permissions
        role_details = COMPANY_ROLE_DETAILS.get(self.role, {})
        return permission_type in role_details.get('permissions', [])


class Notification(models.Model):
    """User notifications system"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='SYSTEM'
    )
    priority = models.CharField(
        max_length=20,
        choices=NOTIFICATION_PRIORITY,
        default='INFO'
    )
    
    # Action/Reference
    action_url = models.URLField(blank=True, null=True)
    action_label = models.CharField(max_length=100, blank=True)
    reference_model = models.CharField(max_length=50, blank=True)  # e.g., 'Payroll', 'Employee'
    reference_id = models.IntegerField(blank=True, null=True)
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Status
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    
    # Delivery tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(blank=True, null=True)
    sms_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notifications'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'accounts_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read', 'archived']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['company']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self, save=True):
        """Mark notification as read"""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            if save:
                self.save(update_fields=['read', 'read_at', 'updated_at'])
    
    def mark_as_unread(self, save=True):
        """Mark notification as unread"""
        if self.read:
            self.read = False
            self.read_at = None
            if save:
                self.save(update_fields=['read', 'read_at', 'updated_at'])
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def days_old(self):
        """Return days since notification was created"""
        return (timezone.now() - self.created_at).days
    
    @property
    def notification_icon(self):
        """Get the icon for this notification type"""
        details = NOTIFICATION_TYPE_DETAILS.get(self.notification_type, {})
        return details.get('icon', 'fas fa-bell')
    
    @property
    def notification_color(self):
        """Get the color for this notification type"""
        details = NOTIFICATION_TYPE_DETAILS.get(self.notification_type, {})
        return details.get('color', 'text-secondary')
    
    @property
    def notification_bg_color(self):
        """Get the background color for this notification type"""
        details = NOTIFICATION_TYPE_DETAILS.get(self.notification_type, {})
        return details.get('bg_color', 'bg-secondary-subtle')
    
    @classmethod
    def create_notification(cls, user, title, message, **kwargs):
        """Helper method to create notifications"""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=kwargs.get('notification_type', 'SYSTEM'),
            priority=kwargs.get('priority', 'INFO'),
            action_url=kwargs.get('action_url'),
            action_label=kwargs.get('action_label'),
            reference_model=kwargs.get('reference_model'),
            reference_id=kwargs.get('reference_id'),
            company=kwargs.get('company'),
            created_by=kwargs.get('created_by'),
            expires_at=kwargs.get('expires_at'),
        )


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
        ("NOTIFICATION_CREATED", "Notification Created"),  # Added
        ("NOTIFICATION_READ", "Notification Read"),        # Added
        ("COMPANY_ACCESS_GRANTED", "Company Access Granted"),  # Added
        ("COMPANY_ACCESS_REVOKED", "Company Access Revoked"),  # Added
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    
    # For company-specific actions
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


# Helper functions for the updated dashboard views
class UserPermissionHelper:
    """Helper class for user permission checks"""
    
    @staticmethod
    def can_access_company(user, company):
        """Check if user can access a specific company"""
        if user.is_global_admin:
            return True
        
        return UserCompany.objects.filter(
            user=user,
            company=company,
            is_active=True
        ).exists()
    
    @staticmethod
    def get_user_companies(user):
        """Get all companies a user can access"""
        if user.is_global_admin:
            from Exactus.company.models import Company
            return Company.objects.all()
        
        return Company.objects.filter(
            authorized_users__user=user,
            authorized_users__is_active=True
        ).distinct()
    
    @staticmethod
    def get_user_company_role(user, company):
        """Get user's role in a specific company"""
        try:
            user_company = UserCompany.objects.get(
                user=user,
                company=company,
                is_active=True
            )
            return user_company.role
        except UserCompany.DoesNotExist:
            return None
    
    @staticmethod
    def has_company_permission(user, company, permission_type):
        """Check if user has specific permission in a company"""
        if user.is_global_admin:
            return True
        
        try:
            user_company = UserCompany.objects.get(
                user=user,
                company=company,
                is_active=True
            )
            return user_company.has_company_permission(permission_type)
        except UserCompany.DoesNotExist:
            return False


# Signals for automatic operations
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=UserCompany)
def log_company_access_granted(sender, instance, created, **kwargs):
    """Log when company access is granted"""
    from .models import AuditLog
    
    if created:
        AuditLog.objects.create(
            user=instance.access_granted_by,
            action="COMPANY_ACCESS_GRANTED",
            target=f"User: {instance.user.username}, Company: {instance.company.trade_name}",
            details=f"Role: {instance.get_role_display()}",
            company=instance.company
        )

@receiver(post_save, sender=UserCompany)
def log_company_access_revoked(sender, instance, **kwargs):
    """Log when company access is revoked (is_active=False)"""
    from .models import AuditLog
    
    if not instance.is_active and hasattr(instance, '_previous_is_active') and instance._previous_is_active:
        AuditLog.objects.create(
            user=None,  # System action
            action="COMPANY_ACCESS_REVOKED",
            target=f"User: {instance.user.username}, Company: {instance.company.trade_name}",
            details=f"Role: {instance.get_role_display()}",
            company=instance.company
        )

@receiver(post_save, sender=Notification)
def log_notification_created(sender, instance, created, **kwargs):
    """Log when notification is created"""
    from .models import AuditLog
    
    if created:
        AuditLog.objects.create(
            user=instance.created_by,
            action="NOTIFICATION_CREATED",
            target=f"Notification: {instance.title}",
            details=f"Type: {instance.get_notification_type_display()}, Priority: {instance.get_priority_display()}",
            company=instance.company
        )

@receiver(post_save, sender=Notification)
def log_notification_read(sender, instance, **kwargs):
    """Log when notification is marked as read"""
    from .models import AuditLog
    
    if instance.read and hasattr(instance, '_previous_read') and not instance._previous_read:
        AuditLog.objects.create(
            user=instance.user,
            action="NOTIFICATION_READ",
            target=f"Notification: {instance.title}",
            details=f"Read at: {instance.read_at}",
            company=instance.company
        )