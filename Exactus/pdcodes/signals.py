# pdcodes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from Exactus.company.models import Company
from Exactus.elements.models import Element
from Exactus.pdcodes.models import PDcode

@receiver(post_save, sender=Company)
def populate_company_default_pdcodes(sender, instance, created, **kwargs):
    """
    When a new Company is created, fetch all Default Elements (1000-4999) 
    from the country and create PDcodes.
    """
    if not created:
        return

    # Fetch country elements
    country_elements = Element.objects.filter(country=instance.country)

    pdcodes_to_create = []
    
    for element in country_elements:
        try:
            code_val = int(element.element_code)
        except (ValueError, TypeError):
            continue

        if 1000 <= code_val <= 4999:
            pdcodes_to_create.append(
                PDcode(
                    company=instance,
                    pdcode_code=element.element_code,
                    pdcode_name=element.element_name,
                    pdcode_description=element.element_description,
                    pdcode_status=element.element_status,
                    pdcode_frequency=element.element_frequency,
                    pdcode_type=element.element_type,
                    pdcode_class=element.element_class,
                    pdcode_category=element.element_category,
                    pdcode_categorytype=element.element_categorytype,
                    
                    pdcode_taxable=element.element_taxable,
                    pdcode_tax_flat=element.element_tax_flat,
                    pdcode_tax_irregular=element.element_tax_irregular,
                    pdcode_social_securitable=element.element_social_securitable,
                    pdcode_pensionable=element.element_pensionable,
                    pdcode_payable=element.element_payable,
                    pdcode_calculate=element.element_calculate,
                    
                    pdcode_account=element.element_account,
                    pdcode_map_code=element.element_map_code,
                    pdcode_gl_account=element.element_gl_account,
                )
            )
    
    # Bulk create for performance
    if pdcodes_to_create:
        PDcode.objects.bulk_create(pdcodes_to_create)