from django.db import models
from django.utils.translation import gettext_lazy as _


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
