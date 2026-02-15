from Exactus.company.forms.base import CompanyForm

def get_company_form_class(country):
    """Registry lookup for company forms."""
    return CompanyForm
