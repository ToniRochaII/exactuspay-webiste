from django.utils.text import slugify
from django.db import models


class PDcode(models.Model):
    """
    Payroll / Deduction code belonging to a specific company.

    Uniqueness rules:
    - (company, pdcode_code) must be unique
    - slug is also unique for clean URLs and admin usage
    """

    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="pdcodes",
    )

    pdcode_code = models.CharField(max_length=50, null=True, blank=True)
    pdcode_description = models.CharField(max_length=150)
    pdcode_name = models.CharField(max_length=150)

    STATUS_CHOICES = [
        ("Visible", "Visible"),
        ("Hidden", "Hidden"),
    ]
    pdcode_status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, blank=True, null=True
    )

    pdcode_account = models.IntegerField(null=True, blank=True)
    pdcode_map_code = models.IntegerField(null=True, blank=True)
    pdcode_gl_account = models.IntegerField(null=True, blank=True)

    FREQUENCY_CHOICES = [
        ("Recurring", "Recurring"),
        ("Non-recurring", "Non-recurring"),
    ]
    pdcode_frequency = models.CharField(
        max_length=15, choices=FREQUENCY_CHOICES, blank=True, null=True
    )

    TYPE_CHOICES = [
        ("Regular", "Regular"),
        ("Irregular", "Irregular"),
    ]
    pdcode_type = models.CharField(
        max_length=50, choices=TYPE_CHOICES, blank=True, null=True
    )

    CLASS_CHOICES = [
        ("Standard", "Standard"),
        ("Statutory", "Statutory"),
    ]
    pdcode_class = models.CharField(
        max_length=50, choices=CLASS_CHOICES, blank=True, null=True
    )

    CATEGORY_CHOICES = [
        ("Payment", "Payment"),
        ("Deduction", "Deduction"),
        ("Notional", "Notional"),
        ("Base", "Base"),
        ("Gross up", "Gross up"),
        ("ER Contribution", "ER Contribution"),
        ("ER Cost", "ER Cost"),
    ]
    pdcode_category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True
    )

    # Flags
    pdcode_taxable = models.BooleanField(default=False)
    pdcode_tax_flat = models.BooleanField(default=False)
    pdcode_tax_irregular = models.BooleanField(default=False)
    pdcode_social_securitable = models.BooleanField(default=False)
    pdcode_pensionable = models.BooleanField(default=False)
    pdcode_payable = models.BooleanField(default=False)
    pdcode_calculate = models.BooleanField(default=False)

    CALCBASETYPE_CHOICES = [
        ("Bracketable", "Bracketable"),
        ("Prorational", "Prorational"),
        ("Pension", "Pension"),
        ("Formulae", "Formulae"),
        ("Base", "Base"),
    ]
    pdcode_categorytype = models.CharField(
        max_length=50, choices=CALCBASETYPE_CHOICES, blank=True, null=True
    )

    # Unique slug for clean URLs / admin usage
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def _build_base_slug(self) -> str:
        base = f"{self.company.company_id}-"
        if self.pdcode_code:
            base += str(self.pdcode_code)
        elif self.pdcode_name:
            base += slugify(self.pdcode_name)
        else:
            base += "pdcode"
        return slugify(base)

    def save(self, *args, **kwargs):
        # Robust slug generation that avoids unique collisions
        if not self.slug:
            base_slug = self._build_base_slug()
            slug_candidate = base_slug
            counter = 2

            from .models import PDcode  # safe self-import in method

            while PDcode.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug_candidate

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pdcode_code} {self.pdcode_description} ({self.company})"

    class Meta:
        ordering = ["pdcode_code"]
        unique_together = ("company", "pdcode_code")
