from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from Exactus.employee.forms.united_kingdom_employee_form import UnitedKingdomEmployeeForm
# 1. IMPORT THE BRAZIL FORM
from Exactus.employee.forms.brazil_employee_form import BrazilEmployeeForm 

def get_employee_form_for_country(country):
    if hasattr(country, "slug"):
        slug = country.slug
    else:
        slug = str(country).lower()

    form_mapping = {
        # United Kingdom
        "united-kingdom": UnitedKingdomEmployeeForm,
        "uk": UnitedKingdomEmployeeForm,
        "gb": UnitedKingdomEmployeeForm,
        "gbr": UnitedKingdomEmployeeForm,

        # 2. ADD BRAZIL MAPPING HERE
        "brazil": BrazilEmployeeForm,
        "br": BrazilEmployeeForm,
        "bra": BrazilEmployeeForm,
    }
    
    # Defaults to BaseEmployeeForm if country not found in mapping
    return form_mapping.get(slug, BaseEmployeeForm)

def get_country_specific_fields(country):
    """
    Used by template to render tabs dynamically.
    """
    FormClass = get_employee_form_for_country(country)
    form = FormClass()

    sections = {
        "personal": [], "address": [], "bank": [], "job": [], "tax": [], "pay": []
    }

    for field_name, field in form.fields.items():
        # Default to 'personal' if data-section is missing
        section = field.widget.attrs.get("data-section", "personal")
        if section in sections:
            sections[section].append(field_name)
    
    return {"sections": sections}