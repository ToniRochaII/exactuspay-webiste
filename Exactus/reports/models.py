from django.db import models
from django.contrib.auth import get_user_model
from Exactus.company.models import Company
from Exactus.country.models import Country
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
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    country = models.ForeignKey(
        Country, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    source_model = models.CharField(
        max_length=50, 
        choices=SOURCE_MODEL_CHOICES,
        default='PayrollResult'
    )

    selected_fields = models.JSONField(
        default=list,
        help_text="List of fields to include in the report"
    )

    # 3. Parameters
    allow_date_range = models.BooleanField(default=True, verbose_name="Filter by Date Range")
    allow_payroll_selection = models.BooleanField(default=True, verbose_name="Filter by Specific Payroll")

    # --- NEW: YEAR TO DATE FLAG ---
    is_ytd = models.BooleanField(
        default=False, 
        verbose_name="Year To Date (YTD)",
        help_text="If checked, values will be summed from the start of the tax year up to the selected period."
    )

    is_comparison = models.BooleanField(
        default=False,
        verbose_name="Comparison Report",
        help_text="If checked, compares the selected period against the previous period."
    )

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        type_label = "YTD" if self.is_ytd else "Period"
        scope = self.country.name if self.country else (self.company.trade_name if self.company else "System")
        return f"{self.name} ({scope} - {type_label})"