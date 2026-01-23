# elements/utils/sync.py
from django.db import transaction
from Exactus.company.models import Company
from Exactus.pdcodes.models import PDcode

def propagate_element_to_companies(element):
    """
    Syncs a specific Element (1000-4900) to PDcodes for all companies in the country.
    This works for both Creation (Insert) and Overwrite (Update).
    """
    # 1. Validation: Only sync numeric codes in range 1000-4900
    try:
        code_val = int(element.element_code)
    except (ValueError, TypeError):
        return 

    if not (1000 <= code_val <= 4900):
        return

    # 2. Find target companies
    companies = Company.objects.filter(country=element.country)
    
    # 3. Update or Create PD Codes
    for company in companies:
        PDcode.objects.update_or_create(
            company=company,
            pdcode_code=element.element_code,
            defaults={
                "pdcode_name": element.element_name,
                "pdcode_description": element.element_description,
                "pdcode_status": element.element_status,
                "pdcode_frequency": element.element_frequency,
                "pdcode_type": element.element_type,
                "pdcode_class": element.element_class,
                "pdcode_category": element.element_category,
                "pdcode_categorytype": element.element_categorytype,
                "pdcode_taxable": element.element_taxable,
                "pdcode_tax_flat": element.element_tax_flat,
                "pdcode_tax_irregular": element.element_tax_irregular,
                "pdcode_social_securitable": element.element_social_securitable,
                "pdcode_pensionable": element.element_pensionable,
                "pdcode_payable": element.element_payable,
                "pdcode_calculate": element.element_calculate,
                "pdcode_account": element.element_account,
                "pdcode_map_code": element.element_map_code,
                "pdcode_gl_account": element.element_gl_account,
            }
        )