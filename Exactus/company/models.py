

from django.db import models
from django.utils.translation import gettext_lazy as _

class ClientGroup(models.Model):
    """
    Represents a group of companies (e.g., 'Smith Holdings') to allow 
    efficient bulk access assignment for Directors/Managers.
    """
    name = models.CharField(max_length=150, unique=True)
    companies = models.ManyToManyField(
        'Company', 
        related_name="client_groups",
        blank=True,
        help_text=_("Select all companies belonging to this client group.")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client Group"
        verbose_name_plural = "Client Groups"


class Company(models.Model):
    """
    Company model representing businesses in different countries.
    """
    
    # --- Choices ---
    ACCOUNT_STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("INACTIVE", "Inactive"),
    ]

    ACCOUNT_ARCHIVE_CHOICES = [
        ("N", "No"),
        ("Y", "Yes"),
    ]
    
    # --- Primary Key ---
    company_id = models.AutoField(primary_key=True)
    
    # --- Identification ---
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
    
    # --- Names ---
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
    logo = models.ImageField(upload_to='company_logos/', blank=True)

    # --- contact ---
    contact = models.CharField(_("contact"), max_length=150, blank=True, null=True)
    phone = models.CharField(_("telephone"), max_length=150, blank=True, null=True)
    email = models.CharField(_("email"), max_length=150, blank=True, null=True)
    website = models.CharField(_("website"), max_length=150, blank=True, null=True)

    # --- Address ---
    building_name = models.CharField(_("Building Name"), max_length=150, blank=True, null=True)
    road_name_1 = models.CharField(_("Road Name 1"), max_length=150, blank=True, null=True)
    road_name_2 = models.CharField(_("Road Name 2"), max_length=150, blank=True, null=True)
    town = models.CharField(_("Town/City"), max_length=100, blank=True, null=True)
    post_code = models.CharField(_("Post Code"), max_length=20, blank=True, null=True)
    county = models.CharField(_("County/State/Province"), max_length=100, blank=True, null=True)
    
    country = models.ForeignKey(
        "country.Country",
        on_delete=models.CASCADE,
        related_name="companies",
        verbose_name=_("Country")
    )
    
    # --- Tax IDs (Generic slots for country-specific usage) ---
    tax_id_01 = models.CharField(_("Tax ID 1"), max_length=50, blank=True, null=True)
    tax_id_02 = models.CharField(_("Tax ID 2"), max_length=50, blank=True, null=True)
    tax_id_03 = models.CharField(_("Tax ID 3"), max_length=50, blank=True, null=True)
    tax_id_04 = models.CharField(_("Tax ID 4"), max_length=50, blank=True, null=True)
    tax_id_05 = models.CharField(_("Tax ID 5"), max_length=50, blank=True, null=True)
    tax_id_06 = models.CharField(_("Tax ID 6"), max_length=50, blank=True, null=True)
    tax_id_07 = models.CharField(_("Tax ID 7"), max_length=50, blank=True, null=True)
    tax_id_08 = models.CharField(_("Tax ID 8"), max_length=50, blank=True, null=True)
    tax_id_09 = models.CharField(_("Tax ID 9"), max_length=50, blank=True, null=True)
    tax_id_10 = models.CharField(_("Tax ID 10"), max_length=50, blank=True, null=True)
    tax_id_11 = models.CharField(_("Tax ID 11"), max_length=50, blank=True, null=True)
    tax_id_12 = models.CharField(_("Tax ID 12"), max_length=50, blank=True, null=True)
    tax_id_13 = models.CharField(_("Tax ID 13"), max_length=50, blank=True, null=True)
    tax_id_14 = models.CharField(_("Tax ID 14"), max_length=50, blank=True, null=True)
    tax_id_15 = models.CharField(_("Tax ID 15"), max_length=50, blank=True, null=True)
    tax_id_16 = models.CharField(_("Tax ID 16"), max_length=50, blank=True, null=True)
    tax_id_17 = models.CharField(_("Tax ID 17"), max_length=50, blank=True, null=True)
    tax_id_18 = models.CharField(_("Tax ID 18"), max_length=50, blank=True, null=True)
    tax_id_19 = models.CharField(_("Tax ID 19"), max_length=50, blank=True, null=True)
    tax_id_20 = models.CharField(_("Tax ID 20"), max_length=50, blank=True, null=True)
    
    # --- RTI (Real Time Information) credentials ---
    rti_user_id = models.CharField(
        _("RTI User ID"), max_length=100, blank=True, null=True,
        help_text=_("Username for payroll reporting")
    )
    
    rti_password = models.CharField(
        _("RTI Password"), max_length=100, blank=True, null=True,
        help_text=_("Password for payroll reporting")
    )
    agent_full_name = models.CharField(
        _("Full Name"), max_length=150, blank=True, null=True,
        help_text=_("Full name for payroll reporting")
    )
    agent_road_name_1 = models.CharField(
        _("Road Name 1"), max_length=150, blank=True, null=True,
        help_text=_("Road name for payroll reporting")
    )
    agent_road_name_2 = models.CharField(
        _("Road Name"), max_length=150, blank=True, null=True,
        help_text=_("Road name for payroll reporting")
    )
    agent_town = models.CharField(
        _("Town"), max_length=150, blank=True, null=True,
        help_text=_("Road name for payroll reporting")
    )
    agent_post_code = models.CharField(
        _("Post Code"), max_length=20, blank=True, null=True,
        help_text=_("Post code for payroll reporting")
    )

    # --- Account Status ---
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
    
    # --- Banking ---
    bank_01 = models.CharField(max_length=100, null=True, blank=True)
    bank_02 = models.CharField(max_length=100, null=True, blank=True)
    bank_03 = models.CharField(max_length=100, null=True, blank=True)
    bank_04 = models.CharField(max_length=100, null=True, blank=True)
    bank_05 = models.CharField(max_length=100, null=True, blank=True)
    bank_06 = models.CharField(max_length=100, null=True, blank=True)
    bank_07 = models.CharField(max_length=100, null=True, blank=True)
    bank_08 = models.CharField(max_length=100, null=True, blank=True)
    bank_09 = models.CharField(max_length=100, null=True, blank=True)
    bank_10 = models.CharField(max_length=100, null=True, blank=True)
    bank_11 = models.CharField(max_length=100, null=True, blank=True)
    bank_12 = models.CharField(max_length=100, null=True, blank=True)
    bank_13 = models.CharField(max_length=100, null=True, blank=True)
    bank_14 = models.CharField(max_length=100, null=True, blank=True)
    bank_15 = models.CharField(max_length=100, null=True, blank=True)
    bank_16 = models.CharField(max_length=100, null=True, blank=True)
    bank_17 = models.CharField(max_length=100, null=True, blank=True)
    bank_18 = models.CharField(max_length=100, null=True, blank=True)
    bank_19 = models.CharField(max_length=100, null=True, blank=True)
    bank_20 = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["trade_name"]
    
    def __str__(self):
        return f"{self.trade_name} ({self.country.name})"