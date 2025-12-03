from django import forms
from Exactus.company.models import Company

# --- REGISTRY ---

COMPANY_FORM_REGISTRY: dict[str, type[forms.ModelForm]] = {}

def register_company_form(country_code: str):
    """
    Usage:
        @register_company_form("GB")
        class CompanyFormGB(CompanyForm):
            ...
    """
    country_code = country_code.upper()

    def decorator(cls):
        COMPANY_FORM_REGISTRY[country_code] = cls
        return cls

    return decorator

# --- UPLOAD FORM CAN STAY GLOBAL (unless you want it per country) ---

class CompanyUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with company data"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database"
    )

def get_company_form_class_for_country(country):
    """
    Given a Country instance, return the appropriate Company form class.
    Fallback: CompanyForm (default).
    """
    # Adjust attribute names to whatever your Country model uses:
    code = getattr(country, "iso2", None) or getattr(country, "code", None)
    if not code:
        return CompanyForm

    code = code.upper()
    return COMPANY_FORM_REGISTRY.get(code, CompanyForm)


# --- DEFAULT FORM ---

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"
        exclude = ["country", "company_id"]
        widgets = {
            "account_status": forms.Select(attrs={"class": "form-select"}),
            "account_archive": forms.Select(attrs={"class": "form-select"}),
        }


# --- COUNTRY-SPECIFIC FORMS ---

@register_company_form("GB")
@register_company_form("GB")
class CompanyFormGB(CompanyForm):
    """
    UK-specific company form for ISO-2 = GB.
    """

    class Meta(CompanyForm.Meta):
        labels = {
            # Base labels inherited, we override only the UK-specific ones
            **getattr(CompanyForm.Meta, "labels", {}),

            "company_id": "Company ID",
            "company_code": "Company Code",
            "company_number": "Company Number",

            "trade_name": "Name",
            "legal_name": "Legal Name",

            "building_name": "Building Name",
            "road_name_1": "Road Name",
            "road_name_2": "Road Name 2",
            "town": "Town",
            "post_code": "Post Code",
            "county": "County",
            "country": "Country",

            # Tax IDs
            "tax_id_1": "Employer PAYE Reference – Office Number",
            "tax_id_2": "Employer PAYE Reference – Reference Number",
            "tax_id_3": "Accounts Office Reference",
            "tax_id_4": "Company Registration Number",
            "tax_id_5": "Company CT UTR",
            "tax_id_6": "SA UTR",
            "tax_id_7": "ECON Reference",
            "tax_id_8": "Eligible for Employer Relief",
            "tax_id_9": "Apprentice Levy Due",
            "tax_id_10": "",  # will be hidden anyway

            "rti_user_id": "RTI Login",
            "rti_password": "RTI Password",
        }

        # Hide tax_id_10
        widgets = {
            **getattr(CompanyForm.Meta, "widgets", {}),

            "tax_id_10": forms.HiddenInput(),
        }


@register_company_form("BR")
class CompanyFormBR(CompanyForm):
    """
    Brazil-specific company form for ISO-2 = BR (English labels).
    """

    class Meta(CompanyForm.Meta):
        labels = {
            **getattr(CompanyForm.Meta, "labels", {}),

            # Identification
            "company_id": "Company ID",
            "company_code": "Company Code",
            "company_number": "Company Number",

            # Names
            "trade_name": "Trade Name (Nome Fantasia)",
            "legal_name": "Legal Name (Razão Social)",

            # Address
            "building_name": "Building / Complement",
            "road_name_1": "Street",
            "road_name_2": "Street (Line 2)",
            "town": "City",
            "post_code": "Post Code (CEP)",
            "county": "District / Neighbourhood (Bairro)",
            "country": "Country",

            # Fiscal Identifiers
            "tax_id_1": "CNPJ",
            "tax_id_2": "State Registration (Inscrição Estadual)",
            "tax_id_3": "Municipal Registration (Inscrição Municipal)",
            "tax_id_4": "Fiscal CNAE Code",
            "tax_id_5": "NIRE",
            "tax_id_6": "Tax Regime (Simples, Real, Presumed)",
            "tax_id_7": "FGTS Code",
            "tax_id_8": "INSS Code",
            "tax_id_9": "eSocial Code",
            "tax_id_10": "",  # hidden

            # System access
            "rti_user_id": "eSocial Username",
            "rti_password": "eSocial Password",
        }

        widgets = {
            **getattr(CompanyForm.Meta, "widgets", {}),
            "tax_id_10": forms.HiddenInput(),  # hidden for BR
        }

    # Optional: CNPJ numeric-length validation
    def clean_tax_id_1(self):
        """Basic CNPJ validation (14 digits)."""
        cnpj = self.cleaned_data.get("tax_id_1")
        if cnpj:
            digits = "".join(filter(str.isdigit, str(cnpj)))
            if len(digits) != 14:
                raise forms.ValidationError("CNPJ must contain 14 digits.")
        return cnpj



