from decimal import Decimal

# UK Class 1 Employee NI (Primary Thresholds)
PRIMARY_THRESHOLD = Decimal("12570")
UPPER_EARNINGS_LIMIT = Decimal("50270")

MAIN_RATE = Decimal("0.08")   # 8%
ADDITIONAL_RATE = Decimal("0.02")  # 2%


def calculate_ni(gross_annual_income: Decimal) -> Decimal:
    """
    Calculate UK Employee National Insurance (Class 1).

    Returns TOTAL annual NI due.

    ⚠️ Does NOT include:
    - Employer NI
    - NI category letters
    - Directors rules
    """

    if gross_annual_income <= PRIMARY_THRESHOLD:
        return Decimal("0.00")

    ni_due = Decimal("0.00")

    # MAIN RATE
    main_band = min(
        gross_annual_income - PRIMARY_THRESHOLD,
        UPPER_EARNINGS_LIMIT - PRIMARY_THRESHOLD
    )

    if main_band > 0:
        ni_due += main_band * MAIN_RATE

    # ADDITIONAL RATE
    if gross_annual_income > UPPER_EARNINGS_LIMIT:
        additional_band = gross_annual_income - UPPER_EARNINGS_LIMIT
        ni_due += additional_band * ADDITIONAL_RATE

    return ni_due.quantize(Decimal("0.01"))
