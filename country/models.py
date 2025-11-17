from django.utils.text import slugify
from django.db import models


class Country(models.Model):
    # ───────────────────────────────
    # Choices
    # ───────────────────────────────
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("IMPLEMENTING", "Implementing"),
        ("INACTIVE", "Inactive"),
    ]

    NUMBERING_FORMAT_CHOICES = [
        ("1,000.00", "1,000.00 (dot as decimal separator)"),
        ("1.000,00", "1.000,00 (comma as decimal separator)"),
    ]

    CURRENCY_POSITION_CHOICES = [
        ("BEFORE", "Currency Code before amount (e.g. EUR 1,000)"),
        ("AFTER", "Currency Code after amount (e.g. 1,000 EUR)"),
    ]

    DATE_FORMAT_CHOICES = [
        ("DD/MM/YYYY", "DD/MM/YYYY"),
        ("MM/DD/YYYY", "MM/DD/YYYY"),
        ("YYYY/MM/DD", "YYYY/MM/DD"),
        ("YYYY/DD/MM", "YYYY/DD/MM"),
    ]

    DECIMAL_CHOICES = [(i, str(i)) for i in range(6)]

    ARCHIVE_FORMAT_CHOICES = [
        ("Y", "YES"),
        ("N", "NO"),
    ]

    # ───────────────────────────────
    # Fields
    # ───────────────────────────────
    iso2_code = models.CharField("ISO 2-Letter Code", max_length=2, unique=True)
    iso3_code = models.CharField("ISO 3-Letter Code", max_length=3, unique=True)
    name = models.CharField("Country Name", max_length=100)
    status = models.CharField("Country Status", max_length=15, choices=STATUS_CHOICES, default="ACTIVE")
    official_language = models.CharField("Official Language", max_length=100)
    currency_name = models.CharField("Currency", max_length=50)
    currency_code = models.CharField("Currency Code", max_length=3)
    fiscal_year_start = models.CharField("Fiscal Year Starts", max_length=20)
    fiscal_year_end = models.CharField("Fiscal Year Ends", max_length=20)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    numbering_format = models.CharField(
        "Numbering Format", max_length=10, choices=NUMBERING_FORMAT_CHOICES, default="1,000.00"
    )
    currency_position = models.CharField(
        "Currency Code Position", max_length=10, choices=CURRENCY_POSITION_CHOICES, default="BEFORE"
    )
    date_format = models.CharField(
        "Date Format", max_length=12, choices=DATE_FORMAT_CHOICES, default="DD/MM/YYYY"
    )
    decimals = models.PositiveSmallIntegerField(
        "Decimal Places", choices=DECIMAL_CHOICES, default=2
    )
    
    archive = models.CharField(
        "Archive Format", max_length=1, choices=ARCHIVE_FORMAT_CHOICES, default="N"
    )

    # ───────────────────────────────
    # Meta & Display
    # ───────────────────────────────

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base = slugify(self.name)
            slug = base
            counter = 1
            from .models import Country  # or skip if inside same file

            while Country.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
