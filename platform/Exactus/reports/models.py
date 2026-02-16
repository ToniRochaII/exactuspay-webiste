
from django.db import models
from django.db.models import Q
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
    Linker table: chooses Layout + Settings for a scope.
    Inheritance resolution: Company -> Country -> System.
    """

    # Scope (exactly one of these, or neither for system)
    company = models.ForeignKey(
        COMPANY_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_configurations",
    )
    country = models.ForeignKey(
        COUNTRY_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_configurations",
    )

    # What this config applies to
    report_type = models.ForeignKey(
        "ReportType",
        on_delete=models.CASCADE,
        related_name="configurations",
    )

    # Which layout/template to render
    selected_layout = models.ForeignKey(
        "ReportLayout",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="configurations",
        help_text=_("The HTML design to use"),
    )

    # Toggle/data options
    data_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Toggle data fields (e.g., {'show_logo': true, 'mask_bank_account': false})"),
    )

    # Derived helper (kept for UI/filtering; always computed)
    LEVEL_SYSTEM = "SYSTEM"
    LEVEL_COUNTRY = "COUNTRY"
    LEVEL_COMPANY = "COMPANY"
    LEVEL_CHOICES = [
        (LEVEL_SYSTEM, _("System Default")),
        (LEVEL_COUNTRY, _("Country Default")),
        (LEVEL_COMPANY, _("Company Specific")),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, editable=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Report Setting")
        verbose_name_plural = _("Report Settings")

        # Fast lookups for resolver: (report_type + scope)
        indexes = [
            models.Index(fields=["report_type", "company"]),
            models.Index(fields=["report_type", "country"]),
            models.Index(fields=["report_type", "level"]),
        ]

        # ✅ Proper uniqueness (works even with NULLs) + guarantees ONE system default per report_type
        constraints = [
            # Company-specific: one per (report_type, company)
            models.UniqueConstraint(
                fields=["report_type", "company"],
                condition=Q(company__isnull=False),
                name="uniq_reportcfg_company_per_type",
            ),
            # Country default: one per (report_type, country) when company is null
            models.UniqueConstraint(
                fields=["report_type", "country"],
                condition=Q(company__isnull=True, country__isnull=False),
                name="uniq_reportcfg_country_per_type",
            ),
            # System default: one per report_type when both are null
            models.UniqueConstraint(
                fields=["report_type"],
                condition=Q(company__isnull=True, country__isnull=True),
                name="uniq_reportcfg_system_per_type",
            ),
        ]

    def clean(self):
        super().clean()

        # ❌ Invalid: both scopes set
        if self.company_id and self.country_id:
            raise ValidationError(_("Choose either company OR country (not both)."))

        # ❌ Invalid: company + country mismatch (optional but strongly recommended)
        # If your Company model has a country FK, enforce consistency:
        company_country_id = getattr(self.company, "country_id", None)
        if self.company_id and self.country_id and company_country_id and company_country_id != self.country_id:
            raise ValidationError(_("Selected company does not belong to the selected country."))

        # Optional: ensure selected_layout matches report_type (if ReportLayout links to ReportType)
        layout_report_type_id = getattr(self.selected_layout, "report_type_id", None)
        if self.selected_layout_id and layout_report_type_id and layout_report_type_id != self.report_type_id:
            raise ValidationError(_("Selected layout does not match this report type."))

    def save(self, *args, **kwargs):
        # Keep level deterministic & always correct
        if self.company_id:
            self.level = self.LEVEL_COMPANY
        elif self.country_id:
            self.level = self.LEVEL_COUNTRY
        else:
            self.level = self.LEVEL_SYSTEM

        # Run model validation (especially important when saving outside ModelForms)
        self.full_clean()

        return super().save(*args, **kwargs)

    def __str__(self):
        scope = "System"
        if self.company_id:
            scope = f"Company {self.company_id}"
        elif self.country_id:
            scope = f"Country {self.country_id}"
        return f"{self.report_type} ({scope})"


