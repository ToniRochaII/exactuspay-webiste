from django.db import models
from django.utils.translation import gettext_lazy as _
from urllib.parse import urljoin

from django.conf import settings


class DemoRequest(models.Model):
    EMPLOYEE_CHOICES = [
        ("<50", "< 50"),
        ("50-250", "50-250"),
        ("250-1000", "250-1000"),
        ("1000+", "1000+"),
    ]

    REGION_CHOICES = [
        ("Not sure yet", _("Not sure yet")),
        ("LATAM", "LATAM"),
        ("Africa", "Africa"),
        ("Asia", "Asia"),
        ("Global", "Global"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    company = models.CharField(max_length=150)
    employees = models.CharField(max_length=20, choices=EMPLOYEE_CHOICES)
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default="Not sure yet")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company} ({self.first_name} {self.last_name})"


class CountryProfile(models.Model):
    slug = models.SlugField(unique=True)
    iso_code = models.CharField(max_length=2, unique=True)
    country_name = models.CharField(max_length=120)
    official_name = models.CharField(max_length=180, blank=True)
    hero_intro = models.TextField()
    overview = models.TextField(blank=True)

    flag_media_path = models.CharField(
        max_length=255,
        blank=True,
        help_text="Relative path inside the ExactusPay media source, e.g. flags/br.svg",
    )

    capital = models.CharField(max_length=120, blank=True)
    primary_languages = models.CharField(max_length=180, blank=True)
    currency = models.CharField(max_length=120, blank=True)
    population_display = models.CharField(max_length=120, blank=True)
    timezones = models.CharField(max_length=180, blank=True)
    dialing_code = models.CharField(max_length=32, blank=True)
    date_format = models.CharField(max_length=32, blank=True)
    internet_domain = models.CharField(max_length=32, blank=True)

    payroll_frequency = models.CharField(max_length=120, blank=True)
    pay_currency = models.CharField(max_length=120, blank=True)
    tax_year = models.CharField(max_length=120, blank=True)
    standard_working_week = models.CharField(max_length=120, blank=True)
    public_holiday_count = models.CharField(max_length=120, blank=True)
    statutory_elements = models.TextField(blank=True)
    employer_contribution_summary = models.TextField(blank=True)
    termination_notice_summary = models.TextField(blank=True)
    minimum_wage_summary = models.CharField(max_length=180, blank=True)

    hero_highlights = models.JSONField(default=list, blank=True)
    payroll_data_points = models.JSONField(default=list, blank=True)
    glance_cards = models.JSONField(default=list, blank=True)
    content_sections = models.JSONField(default=list, blank=True)
    employer_considerations = models.JSONField(default=list, blank=True)

    seo_title = models.CharField(max_length=180, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    last_reviewed_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "country_name"]
        verbose_name = "Country profile"
        verbose_name_plural = "Country profiles"

    def __str__(self) -> str:
        return self.country_name

    @property
    def flag_url(self) -> str:
        if not self.flag_media_path:
            return ""
        if self.flag_media_path.startswith(("http://", "https://", "/")):
            return self.flag_media_path
        return urljoin(settings.MEDIA_URL, self.flag_media_path)

    @property
    def fact_items(self) -> list[dict[str, str]]:
        items = [
            {"label": _("Official country name"), "value": self.official_name},
            {"label": _("Capital"), "value": self.capital},
            {"label": _("Main language(s)"), "value": self.primary_languages},
            {"label": _("Currency"), "value": self.currency},
            {"label": _("Population"), "value": self.population_display},
            {"label": _("Time zone(s)"), "value": self.timezones},
            {"label": _("International dialling code"), "value": self.dialing_code},
            {"label": _("Date format"), "value": self.date_format},
            {"label": _("Internet domain"), "value": self.internet_domain},
        ]
        return [item for item in items if item["value"]]

    @property
    def payroll_intelligence_items(self) -> list[dict[str, str]]:
        items = [
            {"label": _("Payroll frequency"), "value": self.payroll_frequency},
            {"label": _("Typical pay currency"), "value": self.pay_currency},
            {"label": _("Tax year"), "value": self.tax_year},
            {"label": _("Standard working week"), "value": self.standard_working_week},
            {"label": _("Public holiday count"), "value": self.public_holiday_count},
            {"label": _("Common statutory elements"), "value": self.statutory_elements},
            {"label": _("Employer contribution summary"), "value": self.employer_contribution_summary},
            {"label": _("Termination / notice highlights"), "value": self.termination_notice_summary},
            {"label": _("Minimum wage indicator"), "value": self.minimum_wage_summary},
        ]
        static_items = [item for item in items if item["value"]]
        return static_items + list(self.payroll_data_points or [])
