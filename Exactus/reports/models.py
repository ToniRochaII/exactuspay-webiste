from django.db import models
from django.contrib.auth import get_user_model
from Exactus.company.models import Company
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ReportDefinition(models.Model):
    """
    The 'Reported Model'. Stores the structure of a custom report
    so it can be run dynamically with different parameters.
    """
    SOURCE_MODEL_CHOICES = [
        ('PayrollResult', 'Payroll Results (Payslips)'),
        ('Employee', 'Employee Data'),
        ('PayrollPeriod', 'Payroll Periods Summary'),
    ]

    name = models.CharField(max_length=100, verbose_name="Report Name")
    description = models.TextField(blank=True, verbose_name="Description")
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # 1. Source: What are we reporting on?
    source_model = models.CharField(
        max_length=50, 
        choices=SOURCE_MODEL_CHOICES,
        default='PayrollResult'
    )

    # 2. Fields: JSON list of database fields to include
    selected_fields = models.JSONField(
        default=list,
        help_text="List of fields to include in the report"
    )

    # 3. Parameters: What filters can the user apply at runtime?
    allow_date_range = models.BooleanField(default=True, verbose_name="Filter by Date Range")
    allow_payroll_selection = models.BooleanField(default=True, verbose_name="Filter by Specific Payroll")

    # --- FIX IS HERE (SET_NULL) ---
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name