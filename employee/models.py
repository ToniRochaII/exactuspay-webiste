from django.db import models
from company.models import Company


# Employee

class Employee(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees")
    employee_id = models.CharField("Employee ID", max_length=50, null=True, blank=True)
    employee_number = models.IntegerField("Employee Number")
    employee_code = models.IntegerField("Employee Code")
    employee_name = models.CharField("First Name", max_length=100)
    employee_surname = models.CharField("Last Name", max_length=100)

    # ───────────────
    # Personal Info
    # ───────────────
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
    ]
    gender = models.CharField("Gender", max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField("Date of Birth", null=True, blank=True)

    MARITAL_STATUS_CHOICES = [
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced"),
    ]
    marital_status = models.CharField(
        "Marital Status", max_length=20, choices=MARITAL_STATUS_CHOICES, null=True, blank=True
    )

    # ───────────────
    # Address Info
    # ───────────────
    ADDRESS_CHOICES = [
        ("Residential", "Residential"),
        ("Correspondence", "Correspondence"),
    ]
    employee_address_type = models.CharField(
        "Address Type", max_length=20, choices=ADDRESS_CHOICES, null=True, blank=True
    )
    employee_address_01 = models.CharField("Address Line 1", max_length=100, null=True, blank=True)
    employee_address_02 = models.CharField("Address Line 2", max_length=100, null=True, blank=True)
    employee_address_03 = models.CharField("Address Line 3", max_length=100, null=True, blank=True)
    employee_address_04 = models.CharField("Address Line 4", max_length=100, null=True, blank=True)
    employee_address_05 = models.CharField("Address Line 5", max_length=100, null=True, blank=True)
    employee_address_06 = models.CharField("Address Line 6", max_length=100, null=True, blank=True)
    employee_address_07 = models.CharField("Address Line 7", max_length=100, null=True, blank=True)

    # ───────────────
    # Bank Info
    # ───────────────
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

    # ───────────────
    # Job / Payroll Info
    # ───────────────
    department = models.CharField("Department", max_length=100, null=True, blank=True)
    cost_centre = models.CharField("Cost Centre", max_length=100, null=True, blank=True)
    job_title = models.CharField("Job Title", max_length=100, null=True, blank=True)
    position_number = models.CharField("Position Number", max_length=100, null=True, blank=True)
    fte = models.CharField("FTE", max_length=100, null=True, blank=True)

    # ───────────────
    # Tax Info
    # ───────────────
    tax_info_01 = models.CharField(max_length=100, null=True, blank=True)
    tax_info_02 = models.CharField(max_length=100, null=True, blank=True)
    tax_info_03 = models.CharField(max_length=100, null=True, blank=True)
    tax_info_04 = models.CharField(max_length=100, null=True, blank=True)
    tax_info_05 = models.CharField(max_length=100, null=True, blank=True)
    tax_info_06 = models.CharField(max_length=100, null=True, blank=True)
    tax_info_07 = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Employees"
        ordering = ["employee_surname", "employee_name"]

    def __str__(self):
        return f"{self.employee_name} {self.employee_surname} ({self.company.trade_name})"

