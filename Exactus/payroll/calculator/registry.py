# Exactus/payroll/calculator/registry.py
from .countries.br.calculator import BRPayrollCalculator
from .countries.gb.calculator import GBPayrollCalculator

COUNTRY_CALCULATORS = {
    'br': BRPayrollCalculator,
    'gb': GBPayrollCalculator,
    'uk': GBPayrollCalculator,  # Alias for UK
}

def get_calculator(country_code):
    """
    Get calculator for a country
    """
    country_code = country_code.lower()
    
    if country_code not in COUNTRY_CALCULATORS:
        # Try to find by slug or code variations
        from Exactus.country.models import Country
        try:
            country = Country.objects.get(code__iexact=country_code)
            country_code = country.code.lower()
        except Country.DoesNotExist:
            raise NotImplementedError(
                f"No payroll calculator implemented for country code: {country_code}"
            )
    
    return COUNTRY_CALCULATORS.get(country_code)