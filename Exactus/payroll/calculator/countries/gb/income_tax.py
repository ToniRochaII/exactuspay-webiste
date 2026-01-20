from decimal import Decimal

# UK Income Tax bands (England / Wales – can be overridden later)
# This is intentionally SIMPLE and PATCHABLE

PERSONAL_ALLOWANCE = Decimal("12570")
BASIC_RATE_LIMIT = Decimal("50270")
HIGHER_RATE_LIMIT = Decimal("125140")

BASIC_RATE = Decimal("0.20")
HIGHER_RATE = Decimal("0.40")
ADDITIONAL_RATE = Decimal("0.45")


def calculate_income_tax(
    gross_annual_income: Decimal,
    personal_allowance: Decimal = PERSONAL_ALLOWANCE,
) -> Decimal:
    """
    Calculate UK income tax for a single employee (annualised).

    This function:
    - Applies personal allowance
    - Uses standard UK tax bands
    - Returns TOTAL income tax due (Decimal)

    ⚠️ Does NOT handle:
    - Scottish tax
    - Marriage allowance
    - Pension relief
    - Student loans
    """

    if gross_annual_income <= personal_allowance:
        return Decimal("0.00")

    taxable_income = gross_annual_income - personal_allowance
    tax_due = Decimal("0.00")

    # BASIC RATE
    basic_band = min(taxable_income, BASIC_RATE_LIMIT - personal_allowance)
    if basic_band > 0:
        tax_due += basic_band * BASIC_RATE

    # HIGHER RATE
    if gross_annual_income > BASIC_RATE_LIMIT:
        higher_band = min(
            taxable_income - basic_band,
            HIGHER_RATE_LIMIT - BASIC_RATE_LIMIT
        )
        if higher_band > 0:
            tax_due += higher_band * HIGHER_RATE

    # ADDITIONAL RATE
    if gross_annual_income > HIGHER_RATE_LIMIT:
        additional_band = taxable_income - basic_band - higher_band
        if additional_band > 0:
            tax_due += additional_band * ADDITIONAL_RATE

    return tax_due.quantize(Decimal("0.01"))
