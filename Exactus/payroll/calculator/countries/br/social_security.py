
# Exactus/payroll/calculator/countries/br/social_security.py
from decimal import Decimal, ROUND_HALF_UP

# INSS 2024 bands (monthly)
INSS_BANDS_2024 = [
    (Decimal("1412.00"), Decimal("0.075")),    # 7.5%
    (Decimal("2666.68"), Decimal("0.09")),     # 9%
    (Decimal("4000.03"), Decimal("0.12")),     # 12%
    (Decimal("7786.02"), Decimal("0.14")),     # 14%
]

INSS_MAX_CONTRIBUTION = Decimal("908.85")  # Teto

def calculate_inss(gross_salary: Decimal) -> Decimal:
    """
    Calculate Brazilian INSS (social security) using progressive rates
    """
    remaining = gross_salary
    previous_limit = Decimal("0.00")
    total_inss = Decimal("0.00")
    
    for limit, rate in INSS_BANDS_2024:
        if remaining <= Decimal("0"):
            break
        
        band_width = limit - previous_limit
        taxable_in_band = min(remaining, band_width)
        
        total_inss += taxable_in_band * rate
        remaining -= taxable_in_band
        previous_limit = limit
    
    # Apply cap
    return min(total_inss, INSS_MAX_CONTRIBUTION).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)