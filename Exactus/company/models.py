from django.db import models

# Company
class Company(models.Model):
    ACCOUNT_STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("INACTIVE", "Inactive"),
    ]


    ACCOUNT_ARCHIVE_CHOICES = [
        ("N", "NO"),
        ("Y", "YES"),
    ]

    company_id = models.AutoField(primary_key=True)
    company_code = models.CharField("Company Code", max_length=20, unique=False)
    company_number = models.CharField("Company Number", max_length=50, blank=True, null=True)
    trade_name = models.CharField("Trade Name", max_length=150)
    legal_name = models.CharField("Legal Name", max_length=150)
    building_name = models.CharField("Building Name", max_length=150, blank=True, null=True)
    road_name_1 = models.CharField("Road Name 1", max_length=150, blank=True, null=True)
    road_name_2 = models.CharField("Road Name 2", max_length=150, blank=True, null=True)
    town = models.CharField("Town", max_length=100, blank=True, null=True)
    post_code = models.CharField("Post Code", max_length=20, blank=True, null=True)
    county = models.CharField("County", max_length=20, blank=True, null=True)
    country = models.ForeignKey( "country.Country", on_delete=models.CASCADE, related_name="companies")

    tax_id_1 = models.CharField("Tax ID 1", max_length=50, blank=True, null=True)
    tax_id_2 = models.CharField("Tax ID 2", max_length=50, blank=True, null=True)
    tax_id_3 = models.CharField("Tax ID 3", max_length=50, blank=True, null=True)
    tax_id_4 = models.CharField("Tax ID 4", max_length=50, blank=True, null=True)
    tax_id_5 = models.CharField("Tax ID 5", max_length=50, blank=True, null=True)
    tax_id_6 = models.CharField("Tax ID 6", max_length=50, blank=True, null=True)
    tax_id_7 = models.CharField("Tax ID 7", max_length=50, blank=True, null=True)
    tax_id_8 = models.CharField("Tax ID 8", max_length=50, blank=True, null=True)
    tax_id_9 = models.CharField("Tax ID 9", max_length=50, blank=True, null=True)
    tax_id_10 = models.CharField("Tax ID 10", max_length=50, blank=True, null=True)

    rti_user_id = models.CharField("RTI User ID", max_length=100, blank=True, null=True)
    rti_password = models.CharField("RTI Password", max_length=100, blank=True, null=True)

    account_status = models.CharField(
        "Account Status", max_length=10, choices=ACCOUNT_STATUS_CHOICES, default="ACTIVE"
    )

    account_archive = models.CharField(
        "Account Archive", max_length=10, choices=ACCOUNT_ARCHIVE_CHOICES, default="N"
    )

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["trade_name"]

    def __str__(self):
        return f"{self.trade_name} ({self.country.name})"




