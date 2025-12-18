# Exactus/payroll/calculator/countries/br/income_tax.py
from decimal import Decimal, ROUND_HALF_UP

# IRRF 2024 bands (monthly)
IRRF_BANDS_2024 = [
    (Decimal("2259.20"), Decimal("0.00"), Decimal("0.00")),  # Isento
    (Decimal("2828.65"), Decimal("0.075"), Decimal("169.44")),
    (Decimal("3751.05"), Decimal("0.15"), Decimal("381.44")),
    (Decimal("4664.68"), Decimal("0.225"), Decimal("662.77")),
    (Decimal("999999.99"), Decimal("0.275"), Decimal("896.00")),  # Teto
]

def calculate_irrf(taxable_income: Decimal) -> Decimal:
    """
    Calculate Brazilian IRRF (monthly income tax)
    """
    if taxable_income <= IRRF_BANDS_2024[0][0]:
        return Decimal("0.00")
    
    for limit, rate, deduction in IRRF_BANDS_2024:
        if taxable_income <= limit:
            tax = (taxable_income * rate) - deduction
            return max(tax, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    return Decimal("0.00")
