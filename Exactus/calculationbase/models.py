from django.db import models
import datetime
from django.utils.translation import gettext_lazy as _views

from Exactus.country.models import Country
from Exactus.elements.models import Element
from Exactus.regulations.models import Regulations

class CalculationBase(models.Model):

    FREQUENCY_CHOICES = [
        ('Annually', 'Annually'),
        ('Monthly','Monthly'),
        ('Semi-Monthly','Semi-Monthly'),
        ('Fortnightly','Fortnightly'),
        ('Weekly','Weekly'),
    ]

    TABLE_TYPE_CHOICES = [
        ("Single", "Single"),
        ("Parent", "Parent"),
        ("Married", "Married"),
    ]

    SS_CATEGORY_CHOICES = [
        ("A", "A"),
        ("B", "B"),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    regulations = models.ForeignKey(
        Regulations,
        on_delete=models.CASCADE,
        related_name="calculation_bases"
    )

    element = models.ForeignKey(
        Element,
        related_name="calculation_bases",
        on_delete=models.CASCADE
    )

    element_base = models.ForeignKey(
        Element,
        related_name="base_calculation_bases",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )


    base_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, null=True, blank=True)

    # Brackets
    for i in range(16):
        locals()[f"bracket_{i:02}"] = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True) # type: ignore

    # Rates
    for i in range(16):
        locals()[f"rate_{i:02}"] = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True) # type: ignore

    @staticmethod
    def get_default_date():
        return datetime.date.today().isoformat()

    def __str__(self):
        return f"CalculationBase #{self.id}" # type: ignore
