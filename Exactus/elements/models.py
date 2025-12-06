# elements/models.py
from django.utils.text import slugify
from django.db import models
from Exactus.country.models import Country

class Element(models.Model):
    country = models.ForeignKey(
        "country.Country", on_delete=models.CASCADE, related_name="elements"
    )

    element_code = models.CharField(max_length=50, null=True, blank=True)
    element_description = models.CharField(max_length=150)
    element_name = models.CharField(max_length=150)

    STATUS_CHOICES = [
        ('Visible', 'Visible'),
        ('Hidden', 'Hidden'),
    ]
    element_status = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, null=True)

    element_account = models.IntegerField(null=True, blank=True)
    element_map_code = models.IntegerField(null=True, blank=True)
    element_gl_account = models.IntegerField(null=True, blank=True)

    FREQUENCY_CHOICES = [
        ('Recurring', 'Recurring'),
        ('Non-recurring', 'Non-recurring'),
    ]
    element_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, blank=True, null=True)

    TYPE_CHOICES = [
        ('Regular', 'Regular'),
        ('Irregular', 'Irregular'),
    ]
    element_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True, null=True)

    CLASS_CHOICES = [
        ('Standard', 'Standard'),
        ('Statutory', 'Statutory'),
    ]
    element_class = models.CharField(max_length=50, choices=CLASS_CHOICES, blank=True, null=True)

    CATEGORY_CHOICES = [
        ('Payment', 'Payment'),
        ('Deduction', 'Deduction'),
        ('Notional', 'Notional'),
        ('Base', 'Base'),
        ('Gross up', 'Gross up'),
        ('ER Contribution', 'ER Contribution'),
        ('ER Cost', 'ER Cost'),
    ]
    element_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)


    element_taxable = models.BooleanField(default=False)
    element_tax_flat = models.BooleanField(default=False)
    element_tax_irregular = models.BooleanField(default=False)
    element_social_securitable = models.BooleanField(default=False)
    element_pensionable = models.BooleanField(default=False)
    element_payable = models.BooleanField(default=False)
    element_calculate = models.BooleanField(default=False)

    CALCBASETYPE_CHOICES = [
        ('Bracketable', 'Bracketable'),
        ('Prorational', 'Prorational'),
        ('Pension', 'Pension'),
        ('Formulae', 'Formulae'),
        ('Base', 'Base'),
    ]
    element_categorytype = models.CharField(max_length=50, choices=CALCBASETYPE_CHOICES, blank=True, null=True)

    slug = models.SlugField(max_length=100, unique=True, blank=True)
    archive = models.CharField(
        max_length=1,
        choices=[("Y", "YES"), ("N", "NO")],
        default="N",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.country.slug}-{self.element_code or self.element_name}"
            self.slug = slugify(base)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.element_code} {self.element_description} ({self.country})"

    class Meta:
        ordering = ["element_code"]
        unique_together = ("country", "element_code")