from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from Exactus.employee.forms.brazil_employee_form import BrazilEmployeeForm
from Exactus.employee.forms.united_kingdom_employee_form import UnitedKingdomEmployeeForm
from Exactus.employee.forms.argentina_employee_form import ArgentinaEmployeeForm


def normalize_country_slug(country):
    """
    Normalize country input into a lowercase slug.
    """
    if hasattr(country, "slug"):
        slug = country.slug
    elif hasattr(country, "name"):
        slug = country.name
    else:
        slug = str(country)

    return slug.strip().lower().replace(" ", "-")


def get_employee_form_for_country(country):
    """
    Return the correct EmployeeForm class for a given country.
    Falls back safely to BaseEmployeeForm.
    """
    country_slug = normalize_country_slug(country)

    form_mapping = {
        "brazil": BrazilEmployeeForm,
        "brasil": BrazilEmployeeForm,
        "br": BrazilEmployeeForm,

        "united-kingdom": UnitedKingdomEmployeeForm,
        "uk": UnitedKingdomEmployeeForm,
        "gb": UnitedKingdomEmployeeForm,

        "argentina": ArgentinaEmployeeForm,
        "ar": ArgentinaEmployeeForm,
    }

    return form_mapping.get(country_slug, BaseEmployeeForm)


def get_country_specific_fields(country):
    """
    Provide template-friendly metadata for dynamic rendering.

    Returns:
        {
            "form_class": FormClass,
            "sections": {
                "personal": [...],
                "address": [...],
                "bank": [...],
                "job": [...],
                "tax": [...]
            },
            "required_fields": [...]
        }
    """
    form_class = get_employee_form_for_country(country)

    # Instantiate safely (no data, no instance)
    form = form_class()

    sections = {
        "personal": [],
        "address": [],
        "bank": [],
        "job": [],
        "tax": [],
    }

    required_fields = []

    for field_name, field in form.fields.items():
        section = field.widget.attrs.get("data-section", "personal")

        # Guard against bad section values
        if section not in sections:
            section = "personal"

        sections[section].append(field_name)

        # Ignore hidden fields when listing required ones
        if field.required and not field.widget.is_hidden:
            required_fields.append(field_name)

    return {
        "form_class": form_class,
        "sections": sections,
        "required_fields": required_fields,
    }
