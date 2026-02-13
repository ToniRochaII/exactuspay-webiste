from django.db import models

# Create your models here.
import os
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# We use string references to avoid circular imports
# Ensure these match your actual app labels
COMPANY_MODEL = 'company.Company'
COUNTRY_MODEL = 'country.Country'

class ReportCategory(models.Model):
    """
    Groups reports: e.g., 'Payroll Reports', 'Statutory (P45/P60)', 'Internal Ops'
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class ReportType(models.Model):
    """
    Defines the specific report: e.g., 'Standard Payslip', 'General Ledger', 'P45'
    """
    category = models.ForeignKey(ReportCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, help_text="Internal reference, e.g., 'PAYSLIP_STD'")
    description = models.TextField(blank=True)

    # Access Level Flags
    is_employee_accessible = models.BooleanField(default=False, help_text="Can employees see this via ESS?")
    is_statutory = models.BooleanField(default=False, help_text="Is this a legal requirement?")

    def __str__(self):
        return self.name

class ReportLayout(models.Model):
    """
    Stores the actual HTML template files.
    Allows multiple designs for the same ReportType (e.g., 'Payslip Modern', 'Payslip Classic').
    """
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='layouts')
    name = models.CharField(max_length=100, help_text="e.g., 'UK Modern Blue'")
    template_file = models.FileField(upload_to='report_templates/', help_text="Upload the .html file here")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type.name} - {self.name}"

class ReportConfiguration(models.Model):
    """
    The 'Linker' table.
    Determines which Layout + Settings are used for a specific scope.
    Implements the Inheritance: System -> Country -> Company.
    """
    # Scope Fields (Only one should be set, or none for System Default)
    company = models.ForeignKey(COMPANY_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey(COUNTRY_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    # The Logic
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE)
    selected_layout = models.ForeignKey(ReportLayout, on_delete=models.SET_NULL, null=True, help_text="The HTML design to use")
    
    # "Option A" - Toggle Settings
    # Stores JSON like: {"show_logo": true, "mask_bank_account": false, "columns": ["gross", "tax", "net"]}
    data_settings = models.JSONField(default=dict, blank=True, help_text="Toggle data fields (e.g., Show Bonus: True/False)")

    # Hierarchy Level Helper
    LEVEL_CHOICES = [
        ('SYSTEM', 'System Default'),
        ('COUNTRY', 'Country Default'),
        ('COMPANY', 'Company Specific'),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, editable=False)

    class Meta:
        # Prevent duplicate configs for the same scope + report type
        unique_together = [
            ('company', 'report_type'),
            ('country', 'report_type'),
        ]
        verbose_name = "Report Setting"

    def save(self, *args, **kwargs):
        # Auto-detect level
        if self.company:
            self.level = 'COMPANY'
        elif self.country:
            self.level = 'COUNTRY'
        else:
            self.level = 'SYSTEM'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_type} Config ({self.get_level_display()})"




