from Exactus.employee.forms.base_employee_form import BaseEmployeeForm, EmployeeUploadForm
from Exactus.employee.forms.brazil_employee_form import BrazilEmployeeForm
from Exactus.employee.forms.united_kingdom_employee_form import UnitedKingdomEmployeeForm
from Exactus.employee.forms.argentina_employee_form import ArgentinaEmployeeForm


def get_employee_form_for_country(country):
    """
    Returns the appropriate EmployeeForm class for the given country.
    
    Args:
        country: Country object or country slug/name
    
    Returns:
        Form class
    """
    if hasattr(country, 'slug'):
        country_slug = country.slug
    elif hasattr(country, 'name'):
        country_slug = country.name.lower().replace(' ', '-')
    else:
        country_slug = str(country).lower().replace(' ', '-')
    
    form_mapping = {
        'brazil': BrazilEmployeeForm,
        'brasil': BrazilEmployeeForm,
        'united-kingdom': UnitedKingdomEmployeeForm,
        'united kingdom': UnitedKingdomEmployeeForm,
        'uk': UnitedKingdomEmployeeForm,
        'argentina': ArgentinaEmployeeForm,
        'argentine': ArgentinaEmployeeForm,
    }
    
    return form_mapping.get(country_slug, BaseEmployeeForm)


def get_country_specific_fields(country):
    """
    Returns country-specific field configuration for templates.
    
    Args:
        country: Country object or identifier
    
    Returns:
        dict: Field configuration including required fields, sections, etc.
    """
    form_class = get_employee_form_for_country(country)
    form = form_class()
    
    # Group fields by section based on data-section attribute
    sections = {
        'personal': [],
        'address': [],
        'bank': [],
        'job': [],
        'tax': []
    }
    
    for field_name, field in form.fields.items():
        section = field.widget.attrs.get('data-section', 'personal')
        if section in sections:
            sections[section].append(field_name)
    
    return {
        'form_class': form_class,
        'sections': sections,
        'required_fields': [name for name, field in form.fields.items() if field.required],
    }