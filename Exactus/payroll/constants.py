# Exactus/payroll/constants.py

# ======================================================================
# SEMANTIC ELEMENT CODES (CANONICAL SCHEMA)
# ======================================================================
# These codes act as the "Universal Language" for the system.
# Calculators use these abstract codes so they don't depend on specific database IDs.

# 1. INPUT / EARNINGS AGGREGATES
# These are the "Totals" displayed on payslips (e.g., Total Taxable Pay)
EL_GROSS_PAYABLE = '5000'
EL_GROSS_TAXABLE = '5100'
EL_GROSS_NIABLE  = '5200'

# 2. EMPLOYEE TAX ELEMENTS
# Calculated deductions
EL_TAX_FREE_ALLOWANCE = '6000'
EL_INCOME_TAX         = '6100'
EL_NI_EE              = '6200'
EL_PENSION_EE         = '6300'

# 3. EMPLOYEE NET RESULT
EL_NET_PAY = '7000'

# 4. EMPLOYER STATUTORY COSTS
EL_NI_ER = '8000'
EL_PENSION_ER = '8500'

# 5. BASE ELEMENTS (CALCULATION ONLY)
# These are internal "buckets" used for math, usually not printed on payslips.
BASE_PAYABLE = '85000'
BASE_TAXABLE = '85100'
BASE_NIABLE  = '85200'
BASE_PENSION = '85300'

# ======================================================================
# 6. DYNAMIC BASE CONFIGURATION (The "Brain")
# ======================================================================
# This dictionary maps your Element Model fields to specific Bases and Aggregates.
#
# CRITICAL: The keys here MUST match the boolean field names in 
# Exactus.elements.models.Element
#
# Format: 'element_model_field': {'base': '85xxx', 'aggregate': '5xxx' or None}

BASE_MAPPING = {
    # If Element.element_payable is True -> Add to Payable Base & Gross Payable Aggregate
    'element_payable': {
        'base': BASE_PAYABLE, 
        'aggregate': EL_GROSS_PAYABLE
    },
    
    # If Element.element_taxable is True -> Add to Taxable Base & Taxable Gross Aggregate
    'element_taxable': {
        'base': BASE_TAXABLE, 
        'aggregate': EL_GROSS_TAXABLE
    },
    
    # If Element.element_social_securitable is True -> Add to NI Base & NI Gross Aggregate
    'element_social_securitable': {
        'base': BASE_NIABLE,  
        'aggregate': EL_GROSS_NIABLE
    },
    
    # If Element.element_pensionable is True -> Add to Pension Base (No aggregate defined yet)
    'element_pensionable': {
        'base': BASE_PENSION, 
        'aggregate': None 
    },
}