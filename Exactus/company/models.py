"""
Company Models - WITHOUT timestamps for now
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    """
    Company model representing businesses in different countries.
    """
    
    # Choices
    ACCOUNT_STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("INACTIVE", "Inactive"),
    ]

    ACCOUNT_ARCHIVE_CHOICES = [
        ("N", "No"),
        ("Y", "Yes"),
    ]
    
    # Primary Key
    company_id = models.AutoField(primary_key=True)
    
    # Identification
    company_code = models.CharField(
        _("Company Code"),
        max_length=20,
        help_text=_("Unique identifier for the company")
    )
    
    company_number = models.CharField(
        _("Company Number"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Official registration number")
    )
    
    # Names
    trade_name = models.CharField(
        _("Trade Name"),
        max_length=150,
        help_text=_("Business/trading name")
    )
    
    legal_name = models.CharField(
        _("Legal Name"),
        max_length=150,
        help_text=_("Registered legal name")
    )
    
    # Address
    building_name = models.CharField(
        _("Building Name"),
        max_length=150,
        blank=True,
        null=True
    )
    
    road_name_1 = models.CharField(
        _("Road Name 1"),
        max_length=150,
        blank=True,
        null=True
    )
    
    road_name_2 = models.CharField(
        _("Road Name 2"),
        max_length=150,
        blank=True,
        null=True
    )
    
    town = models.CharField(
        _("Town/City"),
        max_length=100,
        blank=True,
        null=True
    )
    
    post_code = models.CharField(
        _("Post Code"),
        max_length=20,
        blank=True,
        null=True
    )
    
    county = models.CharField(
        _("County/State/Province"),
        max_length=100,
        blank=True,
        null=True
    )
    
    country = models.ForeignKey(
        "country.Country",
        on_delete=models.CASCADE,
        related_name="companies",
        verbose_name=_("Country")
    )
    
    # Tax IDs (flexible for different countries)
    tax_id_1 = models.CharField(_("Tax ID 1"), max_length=50, blank=True, null=True)
    tax_id_2 = models.CharField(_("Tax ID 2"), max_length=50, blank=True, null=True)
    tax_id_3 = models.CharField(_("Tax ID 3"), max_length=50, blank=True, null=True)
    tax_id_4 = models.CharField(_("Tax ID 4"), max_length=50, blank=True, null=True)
    tax_id_5 = models.CharField(_("Tax ID 5"), max_length=50, blank=True, null=True)
    tax_id_6 = models.CharField(_("Tax ID 6"), max_length=50, blank=True, null=True)
    tax_id_7 = models.CharField(_("Tax ID 7"), max_length=50, blank=True, null=True)
    tax_id_8 = models.CharField(_("Tax ID 8"), max_length=50, blank=True, null=True)
    tax_id_9 = models.CharField(_("Tax ID 9"), max_length=50, blank=True, null=True)
    tax_id_10 = models.CharField(_("Tax ID 10"), max_length=50, blank=True, null=True)
    
    # RTI (Real Time Information) credentials
    rti_user_id = models.CharField(
        _("RTI User ID"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Username for payroll reporting")
    )
    
    rti_password = models.CharField(
        _("RTI Password"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Password for payroll reporting")
    )
    
    # Account Status
    account_status = models.CharField(
        _("Account Status"),
        max_length=10,
        choices=ACCOUNT_STATUS_CHOICES,
        default="ACTIVE"
    )
    
    account_archive = models.CharField(
        _("Account Archive"),
        max_length=10,
        choices=ACCOUNT_ARCHIVE_CHOICES,
        default="N"
    )
    
    # NOTE: REMOVED timestamp fields to fix migration issues
    # created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    # updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["trade_name"]
    
    def __str__(self):
        return f"{self.trade_name} ({self.country.name})"