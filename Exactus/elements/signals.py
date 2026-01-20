from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Element

@receiver(post_save, sender=Element)
def create_shadow_elements(sender, instance, created, **kwargs):
    """
    Automatically creates associated shadow elements (1X, 2X, 8X, 9X)
    when a new primary element is created.
    """
    # 1. Stop if this is an update OR if the element is already a shadow element
    if not created or instance.is_auto_generated:
        return

    # 2. Run generation after the transaction commits
    transaction.on_commit(lambda: _generate_shadows(instance))

def _generate_shadows(parent):
    """
    Internal function to generate the 4 types of shadow elements based on prefix rules.
    """
    def create_shadow(prefix, suffix_name, category='Notional', type_override=None):
        # Construct new code (e.g., "9" + "5001" = "95001")
        new_code = f"{prefix}{parent.element_code}"
        
        # Prevent duplicates
        if Element.objects.filter(country=parent.country, element_code=new_code).exists():
            return

        Element.objects.create(
            country=parent.country,
            element_code=new_code,
            element_name=f"{suffix_name} - {parent.element_name}",
            element_description=f"Auto-generated {suffix_name} for {parent.element_code}",
            
            # Inherit settings from parent
            element_account=parent.element_account, 
            element_gl_account=parent.element_gl_account,
            
            # Shadow settings (Hidden, Recurring, Notional/Base)
            element_status='Hidden',
            element_frequency='Recurring',
            element_type=type_override or 'Regular',
            element_class='Standard',
            element_category=category,
            
            # Flags: Shadows are calculation tools, not usually payable directly
            element_taxable=False,
            element_payable=False,
            element_calculate=True, 
            
            # Mark as auto-generated to prevent recursion
            is_auto_generated=True
        )

    # --- LOGIC RULES ---

    # Try to parse code as integer for range checks
    try:
        code_val = int(parent.element_code)
    except (ValueError, TypeError):
        # If code is non-numeric (e.g., "BASIC"), we skip 8X/9X generation
        # but might still want 1X/2X if your business logic supports string codes.
        return 

    # 1. ALWAYS Create 1X (YTD Value)
    # Applies to almost all numeric payment/deduction codes to track Fiscal Year totals
    create_shadow("1", "YTD", category='Notional')

    # 2. ALWAYS Create 2X (Cumulative Value)
    # Applies to almost all numeric codes for custom scope tracking
    create_shadow("2", "Cumulative", category='Notional')

    # 3. Create 8X (Base used to calculate X)
    # Rule: applies to 5000–9999 (Gross totals & derived figures)
    if 5000 <= code_val <= 9999:
        create_shadow("8", "Calc Base", category='Base')

    # 4. Create 9X (Base used to calculate Employer costs)
    # Rule: Base for Employer Costs (8000–9999) OR Gross elements (5000-7999)
    # Since 5000-7999 often serve as the base for employer taxes, we encompass the full range.
    if 5000 <= code_val <= 9999:
        create_shadow("9", "ER Cost Base", category='Base')