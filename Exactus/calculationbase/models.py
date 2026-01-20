from django.db import models
import datetime
from django.utils.translation import gettext_lazy as _

from Exactus.country.models import Country
from Exactus.elements.models import Element
from Exactus.regulations.models import Regulations

class CalculationBase(models.Model):

    FREQUENCY_CHOICES = [
        ('Annually', 'Annually'),
        ('Monthly', 'Monthly'),
        ('Semi-Monthly', 'Semi-Monthly'),
        ('Fortnightly', 'Fortnightly'),
        ('Weekly', 'Weekly'),
    ]

    ROUNDING_CHOICES = [
        ('None', 'None'), 
        ('Round up', 'Round up'), 
        ('Round down', 'Round down')
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

    # --- NEW FIELDS (Required for TaxEngine) ---
    # Added blank=True to prevent validation errors if not provided in form
    rounding_base = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    rounding_bracket = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    rounding_taxed = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    # -------------------------------------------

    # Brackets
    bracket_00 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_00 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_01 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_01 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_02 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_02 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_03 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_03 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_04 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_04 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_05 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_05 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_06 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_06 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_07 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_07 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_08 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_08 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_09 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_09 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_10 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_10 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_11 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_11 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_12 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_12 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_13 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_13 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_14 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_14 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)
    
    bracket_15 = models.DecimalField(max_digits=15, decimal_places=3, default=0, null=True, blank=True)
    rate_15 = models.DecimalField(max_digits=15, decimal_places=4, default=0, null=True, blank=True)

    @staticmethod
    def get_default_date():
        return datetime.date.today().isoformat()

    def __str__(self):
        return f"CalculationBase #{self.id} ({self.element.name})"