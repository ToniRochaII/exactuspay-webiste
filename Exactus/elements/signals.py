# elements/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Element
from Exactus.elements.utils.sync import propagate_element_to_companies

@receiver(post_save, sender=Element)
def sync_element_on_create(sender, instance, created, **kwargs):
    """
    Automatic Sync: Only runs when the Element is FIRST created.
    Edits are handled manually by the view to prevent unwanted overwrites.
    """
    # CRITICAL: This check ensures we do NOT overwrite on edit
    if not created:
        return

    # If created, propagate to all companies immediately
    transaction.on_commit(lambda: propagate_element_to_companies(instance))


@receiver(post_save, sender=Element)
def create_shadow_elements(sender, instance, created, **kwargs):
    """
    Automatically creates associated shadow elements (1X, 2X, 8X, 9X)
    when a new primary element is created.
    """
    if not created or instance.is_auto_generated:
        return

    transaction.on_commit(lambda: _generate_shadows(instance))

def _generate_shadows(parent):
    """
    Internal function to generate the 4 types of shadow elements based on prefix rules.
    """
    def create_shadow(prefix, suffix_name, category='Notional', categorytype='Base', type_override=None):
        new_code = f"{prefix}{parent.element_code}"
        
        if Element.objects.filter(country=parent.country, element_code=new_code).exists():
            return

        Element.objects.create(
            country=parent.country,
            element_code=new_code,
            element_name=f"{suffix_name} - {parent.element_name}",
            element_description=f"{suffix_name} for {parent.element_name}",
            element_status='Hidden',
            element_frequency='Recurring',
            element_type=type_override or 'Regular',
            element_class='Standard',
            element_category=category,
            element_categorytype=categorytype,
            element_taxable=False,
            element_payable=False,
            element_calculate=True, 
            is_auto_generated=True,
            # Inherit accounting from parent so it maps correctly
            element_account=parent.element_account,
            element_gl_account=parent.element_gl_account
        )

    try:
        code_val = int(parent.element_code)
    except (ValueError, TypeError):
        return 

    # 1. ALWAYS Create 1X (YTD) & 2X (Cumulative)
    create_shadow("1", "YTD", category='Notional', categorytype='Formulae')
    create_shadow("2", "Cumulative", category='Notional', categorytype='Formulae')

    # 2. Create 8X & 9X for Gross/Base elements (5000-9999)
    if 5000 <= code_val <= 9999:
        create_shadow("8", "Base ", category='Base', categorytype='Base')
        create_shadow("9", "Base YTD", category='Base', categorytype='Base')