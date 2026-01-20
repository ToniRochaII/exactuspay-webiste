# Exactus/company/forms/__init__.py

from Exactus.company.forms.base_company_form import BaseCompanyForm
from Exactus.company.forms.br_company_form import BrazilCompanyForm
from Exactus.company.forms.gb_company_form import UnitedKingdomCompanyForm
# Import other countries here...


def get_company_form_for_country(country):
    """
    Returns the specific CompanyForm class for a given country object or slug.
    """
    # Handle input whether it's an object or a string slug
    iso_code = getattr(country, "iso2_code", str(country)).upper()
    
    # Mapping Registry
    _forms = {
        "BR": BrazilCompanyForm,
        "GB": UnitedKingdomCompanyForm,
        "UK": UnitedKingdomCompanyForm, # Handle both ISO and Slug if needed
        # "AR": ArgentinaCompanyForm, 
        # "US": UnitedStatesCompanyForm,
    }

    return _forms.get(iso_code, BaseCompanyForm)