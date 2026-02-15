from django.db import models
import datetime
from django.utils.translation import gettext_lazy as _

from Exactus.country.models import Country
from Exactus.elements.models import Element
from Exactus.regulations.models import Regulations

class CalculationBase(models.Model):

    FREQUENCY_CHOICES = [
        ('Weekly', 'Weekly'),
        ('Fortnightly', 'Fortnightly'),
        ('Semi-Monthly', 'Semi-Monthly'),
        ('Four-weekly', 'Four-weekly'),
        ('Monthly', 'Monthly'),
    ]

    ROUNDING_CHOICES = [
        ('None', 'Standard (Half Up)'), 
        ('Round up', 'Round Up'), 
        ('Round down', 'Round Down')
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    regulations = models.ForeignKey(Regulations, on_delete=models.CASCADE, related_name="calculation_bases")
    element = models.ForeignKey(Element, related_name="calculation_bases", on_delete=models.CASCADE)
    element_base = models.ForeignKey(Element, related_name="base_calculation_bases", on_delete=models.CASCADE, null=True, blank=True)
    base_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, null=True, blank=True)

    # --- GLOBAL SETTINGS (The "Set up" section of your sheet) ---
    rounding_base = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    # Added blank=True below
    rounding_base_decimals = models.IntegerField(default=2, blank=True)
    
    rounding_taxed = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    # Added blank=True below
    rounding_taxed_decimals = models.IntegerField(default=2, blank=True)

    # --- BRACKET DEFINITIONS (00 to 15) ---
    # Each bracket has: Limit, Rate, Bracket Rounding, Result Rounding
    
    # Bracket 00
    bracket_00 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_00 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_00 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_00 = models.IntegerField(default=2, blank=True)
    round_result_logic_00 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_00 = models.IntegerField(default=2, blank=True)

    # Bracket 01
    bracket_01 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_01 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_01 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_01 = models.IntegerField(default=2, blank=True)
    round_result_logic_01 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_01 = models.IntegerField(default=2, blank=True)

    # Bracket 02
    bracket_02 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_02 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_02 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_02 = models.IntegerField(default=2, blank=True)
    round_result_logic_02 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_02 = models.IntegerField(default=2, blank=True)

    # Bracket 03
    bracket_03 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_03 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_03 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_03 = models.IntegerField(default=2, blank=True)
    round_result_logic_03 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_03 = models.IntegerField(default=2, blank=True)

    # Bracket 04
    bracket_04 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_04 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_04 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_04 = models.IntegerField(default=2, blank=True)
    round_result_logic_04 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_04 = models.IntegerField(default=2, blank=True)

    # Bracket 05
    bracket_05 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_05 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_05 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_05 = models.IntegerField(default=2, blank=True)
    round_result_logic_05 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_05 = models.IntegerField(default=2, blank=True)

    # Bracket 06
    bracket_06 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_06 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_06 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_06 = models.IntegerField(default=2, blank=True)
    round_result_logic_06 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_06 = models.IntegerField(default=2, blank=True)

    # Bracket 07
    bracket_07 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_07 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_07 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_07 = models.IntegerField(default=2, blank=True)
    round_result_logic_07 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_07 = models.IntegerField(default=2, blank=True)

    # Bracket 08
    bracket_08 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_08 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_08 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_08 = models.IntegerField(default=2, blank=True)
    round_result_logic_08 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_08 = models.IntegerField(default=2, blank=True)

    # Bracket 09
    bracket_09 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_09 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_09 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_09 = models.IntegerField(default=2, blank=True)
    round_result_logic_09 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_09 = models.IntegerField(default=2, blank=True)

    # Bracket 10
    bracket_10 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_10 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_10 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_10 = models.IntegerField(default=2, blank=True)
    round_result_logic_10 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_10 = models.IntegerField(default=2, blank=True)

    # Bracket 11
    bracket_11 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_11 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_11 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_11 = models.IntegerField(default=2, blank=True)
    round_result_logic_11 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_11 = models.IntegerField(default=2, blank=True)

    # Bracket 12
    bracket_12 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_12 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_12 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_12 = models.IntegerField(default=2, blank=True)
    round_result_logic_12 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_12 = models.IntegerField(default=2, blank=True)

    # Bracket 13
    bracket_13 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_13 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_13 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_13 = models.IntegerField(default=2, blank=True)
    round_result_logic_13 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_13 = models.IntegerField(default=2, blank=True)

    # Bracket 14
    bracket_14 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_14 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_14 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_14 = models.IntegerField(default=2, blank=True)
    round_result_logic_14 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_14 = models.IntegerField(default=2, blank=True)

    # Bracket 15
    bracket_15 = models.DecimalField(max_digits=30, decimal_places=2, default=0, null=True, blank=True)
    rate_15 = models.DecimalField(max_digits=30, decimal_places=6, default=0, null=True, blank=True)
    round_bracket_logic_15 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_bracket_dec_15 = models.IntegerField(default=2, blank=True)
    round_result_logic_15 = models.CharField(max_length=15, choices=ROUNDING_CHOICES, default='None', blank=True)
    round_result_dec_15 = models.IntegerField(default=2, blank=True)

    @staticmethod
    def get_default_date():
        return datetime.date.today().isoformat()

    def __str__(self):
        return f"CalculationBase #{self.id} ({self.element.name})"