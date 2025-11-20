from django.utils.text import slugify
from django.db import models
from company.models import Company

class PDcode(models.Model):
    company= models.ForeignKey(
        "company.Company", on_delete=models.CASCADE, related_name="pdcodes"
    )

    pdcode_code = models.CharField(max_length=50, null=True, blank=True)
    pdcode_description = models.CharField(max_length=150)
    pdcode_name = models.CharField(max_length=150)

    STATUS_CHOICES = [
        ('Visible', 'Visible'),
        ('Hidden', 'Hidden'),
    ]
    pdcode_status = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, null=True)

    pdcode_account = models.IntegerField(null=True, blank=True)
    pdcode_map_code = models.IntegerField(null=True, blank=True)
    pdcode_gl_account = models.IntegerField(null=True, blank=True)

    FREQUENCY_CHOICES = [
        ('Recurring', 'Recurring'),
        ('Non-recurring', 'Non-recurring'),
    ]
    pdcode_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, blank=True, null=True)

    TYPE_CHOICES = [
        ('Regular', 'Regular'),
        ('Irregular', 'Irregular'),
    ]
    pdcode_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True, null=True)

    CLASS_CHOICES = [
        ('Standard', 'Standard'),
        ('Statutory', 'Statutory'),
    ]
    pdcode_class = models.CharField(max_length=50, choices=CLASS_CHOICES, blank=True, null=True)

    CATEGORY_CHOICES = [
        ('Payment', 'Payment'),
        ('Deduction', 'Deduction'),
        ('Notional', 'Notional'),
        ('Base', 'Base'),
        ('Gross up', 'Gross up'),
        ('ER Contribution', 'ER Contribution'),
        ('ER Cost', 'ER Cost'),
    ]
    pdcode_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)

    # Flags
    pdcode_taxable = models.BooleanField(default=False)
    pdcode_tax_flat = models.BooleanField(default=False)
    pdcode_tax_irregular = models.BooleanField(default=False)
    pdcode_social_securitable = models.BooleanField(default=False)
    pdcode_pensionable = models.BooleanField(default=False)
    pdcode_payable = models.BooleanField(default=False)
    pdcode_calculate = models.BooleanField(default=False)

    CALCBASETYPE_CHOICES = [
        ('Bracketable', 'Bracketable'),
        ('Prorational', 'Prorational'),
        ('Pension', 'Pension'),
        ('Formulae', 'Formulae'),
        ('Base', 'Base'),
    ]
    pdcode_categorytype = models.CharField(max_length=50, choices=CALCBASETYPE_CHOICES, blank=True, null=True)

    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.company.id}-{self.pdcode_code or self.pdcode_name}"
            self.slug = slugify(base)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pdcode_code} {self.pdcode_description} ({self.company})"

    class Meta:
        ordering = ["pdcode_code"]
        unique_together = ("company", "pdcode_code")