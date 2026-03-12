


def get_company_form_for_country(country):
    """
    Return the correct CompanyForm class for a given country.
    """
    from Exactus.company.forms.united_kingdom_company_form import UnitedKingdomCompanyForm
    from Exactus.company.forms.brazil_company_form import BrazilCompanyForm
    from Exactus.company.forms.base_company_form import BaseCompanyForm

    form_map = {
        "united-kingdom": UnitedKingdomCompanyForm,
        "uk": UnitedKingdomCompanyForm,
        "gb": UnitedKingdomCompanyForm,

        "brazil": BrazilCompanyForm,
        "brasil": BrazilCompanyForm,
        "br": BrazilCompanyForm,


        'DEFAULT': BaseCompanyForm,
    }

    # Handle Country objects
    if hasattr(country, 'code'):
        country_code = country.code.upper()
    # Handle strings
    elif isinstance(country, str):
        country_code = country.upper()
    else:
        # Unknown type, return base form
        return BaseCompanyForm
    
    return form_map.get(country_code, form_map['DEFAULT'])