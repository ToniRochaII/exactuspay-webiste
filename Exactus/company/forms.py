from django import forms
from Exactus.company.models import Company

# ────────────────────────────────────────────────────────────────
# ⚙️ Form Registry & Factory
# ────────────────────────────────────────────────────────────────

COMPANY_FORM_REGISTRY: dict[str, type[forms.ModelForm]] = {}

def register_company_form(country_code: str):
    """Decorator to register a form class for a specific country ISO code."""
    country_code = country_code.upper()
    def decorator(cls):
        COMPANY_FORM_REGISTRY[country_code] = cls
        return cls
    return decorator

def get_company_form_class_for_country(country):
    """
    Returns the specific form class for a country, or the default CompanyForm.
    """
    # Adjust 'iso2_code' if your Country model uses 'code' or 'iso2'
    code = getattr(country, "iso2_code", None) 
    if not code:
        return CompanyForm

    code = code.upper()
    return COMPANY_FORM_REGISTRY.get(code, CompanyForm)

# ────────────────────────────────────────────────────────────────
# 📄 Upload Form
# ────────────────────────────────────────────────────────────────

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

# ────────────────────────────────────────────────────────────────
# 📝 Base Company Form
# ────────────────────────────────────────────────────────────────

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"
        exclude = ["country", "company_id"]
        widgets = {
            "account_status": forms.Select(attrs={"class": "form-select"}),
            "account_archive": forms.Select(attrs={"class": "form-select"}),
        }

# ────────────────────────────────────────────────────────────────
# 🌍 Country Specific Forms
# ────────────────────────────────────────────────────────────────

@register_company_form("GB")
class CompanyFormGB(CompanyForm):
    """UK-specific company form (ISO: GB)."""
    class Meta(CompanyForm.Meta):
        labels = {
            **getattr(CompanyForm.Meta, "labels", {}),
            "company_number": "Company Registration Number",
            "tax_id_1": "Employer PAYE Reference – Office Number",
            "tax_id_2": "Employer PAYE Reference – Reference Number",
            "tax_id_3": "Accounts Office Reference",
            "tax_id_4": "Corporation Tax UTR",
            # Add other specific labels as needed
        }
        widgets = {
            **getattr(CompanyForm.Meta, "widgets", {}),
            "tax_id_10": forms.HiddenInput(),
        }

@register_company_form("BR")
class CompanyFormBR(CompanyForm):
    """Brazil-specific company form (ISO: BR)."""
    class Meta(CompanyForm.Meta):
        labels = {
            **getattr(CompanyForm.Meta, "labels", {}),
            "trade_name": "Trade Name (Nome Fantasia)",
            "legal_name": "Legal Name (Razão Social)",
            "tax_id_1": "CNPJ",
            "tax_id_2": "Inscrição Estadual",
            "tax_id_3": "Inscrição Municipal",
        }
    
    def clean_tax_id_1(self):
        """Basic CNPJ validation."""
        cnpj = self.cleaned_data.get("tax_id_1")
        if cnpj:
            digits = "".join(filter(str.isdigit, str(cnpj)))
            if len(digits) != 14:
                raise forms.ValidationError("CNPJ must contain 14 digits.")
        return cnpj

@register_company_form("AR")
class CompanyFormAR(CompanyForm):
    """Argentina-specific company form (ISO: AR)."""
    class Meta(CompanyForm.Meta):
        labels = {
            **getattr(CompanyForm.Meta, "labels", {}),
            "trade_name": "Nombre Comercial",
            "legal_name": "Razón Social",
            "tax_id_1": "CUIT",
            "tax_id_2": "Ingresos Brutos",
        }

    def clean_tax_id_1(self):
        """Basic CUIT validation."""
        cuit = self.cleaned_data.get("tax_id_1")
        if cuit:
            digits = "".join(filter(str.isdigit, str(cuit)))
            if len(digits) != 11:
                raise forms.ValidationError("CUIT must contain 11 digits.")
        return cuit