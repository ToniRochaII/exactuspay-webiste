# Exactus/company/forms.py
from django import forms
from Exactus.company.models import Company
from Exactus.company.registry import register_company_form

# ================================================================
# 🌍 GLOBAL COUNTRY CONFIGURATION
# ================================================================

COUNTRY_FIELD_RULES = {
    "BR": {
        "labels": {
            "company_number": "Número da Empresa",
            "company_code": "Código da Empresa",
            "trade_name": "Nome Fantasia",
            "legal_name": "Razão Social",
            "tax_id_1": "CNPJ",
            "tax_id_2": "Inscrição Estadual",
            "tax_id_3": "Inscrição Municipal",
            "building_name": "Building Name",
            "road_name_1": "Road Name 1",
            "town": "Town",
            "post_code": "Post ",
            "county": "Estado",
            "account_status": "Status da Conta",
            "account_archive": "Arquivado?",
            "logo": "Logotipo",
        },
        "hidden": [
            "tax_id_4", "tax_id_5", "tax_id_6", "tax_id_7", "tax_id_8", "tax_id_9",
            "tax_id_10", "tax_id_11", "tax_id_12", "tax_id_13",
            "tax_id_14", "tax_id_15", "tax_id_16", "tax_id_17",
            "tax_id_18", "tax_id_19", "tax_id_20",
            "road_name_2",
            "rti_user_id",
            "rti_password",
        ],
        "placeholders": {
            "tax_id_1": "00.000.000/0000-00",
            "tax_id_2": "Isento ou IE",
            "tax_id_3": "Opcional",
        },
        "helptext": {
            "tax_id_1": "Informe o CNPJ completo da empresa.",
            "tax_id_2": "Número da Inscrição Estadual (IE).",
            "tax_id_3": "Inscrição Municipal (IM), se aplicável.",
        },
    },

    "GB": {
        "labels": {
            "company_number": "Company Registration Number",
            "tax_id_1": "PAYE Office Number",
            "tax_id_2": "PAYE Reference Number",
            "tax_id_3": "Accounts Office Reference",
            "tax_id_4": "Corporation CT UTR",
            "tax_id_5": "SA UTR",
            "tax_id_6": "ECON Reference",
        },
        "hidden": [
            "tax_id_7", "tax_id_8", "tax_id_9",
            "tax_id_10", "tax_id_11", "tax_id_12",
            "tax_id_13", "tax_id_14", "tax_id_15",
            "tax_id_16", "tax_id_17", "tax_id_18",
            "tax_id_19", "tax_id_20",
        ],
        "helptext": {
            "tax_id_1": "Office Number",
            "tax_id_2": "Reference Number",
        },
    },

    "AR": {
        "labels": {
            "trade_name": "Nombre Comercial",
            "legal_name": "Razón Social",
            "tax_id_1": "CUIT",
            "tax_id_2": "Ingresos Brutos",
        },
        "hidden": [
            "tax_id_3", "tax_id_4", "tax_id_5", "tax_id_6", "tax_id_7",
            "tax_id_8", "tax_id_9", "tax_id_10",
            "tax_id_11", "tax_id_12", "tax_id_13",
            "tax_id_14", "tax_id_15", "tax_id_16",
            "tax_id_17", "tax_id_18", "tax_id_19", "tax_id_20",
        ],
        "helptext": {
            "tax_id_1": "CUIT must contain 11 digits.",
        },
        "placeholders": {
            "tax_id_1": "00-00000000-0",
        },
    },
}


# ================================================================
# 📄 UPLOAD FORM
# ================================================================

class CompanyUploadForm(forms.Form):
    file = forms.FileField(label="CSV File")
    dry_run = forms.BooleanField(required=False, initial=False, label="Dry Run")


# ================================================================
# 🏢 BASE COMPANY FORM (GLOBAL LOGIC APPLIED)
# ================================================================

class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = "__all__"
        exclude = ["country", "company_id"]
        widgets = {
            "account_status": forms.Select(attrs={"class": "form-select"}),
            "account_archive": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        # Country is injected by the view
        self.country_instance = kwargs.pop("country", None)
        super().__init__(*args, **kwargs)

        # Apply country rules if we have a country
        if self.country_instance:
            self._apply_country_rules()

    def _get_country_iso(self) -> str:
        """Try multiple attribute names to get the 2-letter ISO code."""
        c = self.country_instance
        if not c:
            return ""

        iso = (
            getattr(c, "iso2_code", None)
            or getattr(c, "iso2", None)
            or getattr(c, "code", None)
            or ""
        )
        return str(iso).upper().strip()

    def _apply_country_rules(self):
        iso = self._get_country_iso()
        if not iso:
            return

        rules = COUNTRY_FIELD_RULES.get(iso)
        if not rules:
            return

        # 1. Labels
        for field_name, new_label in rules.get("labels", {}).items():
            if field_name in self.fields:
                self.fields[field_name].label = new_label

        # 2. Hidden fields
        for field_name in rules.get("hidden", []):
            if field_name in self.fields:
                self.fields[field_name].widget = forms.HiddenInput()

        # 3. Placeholders
        for field_name, placeholder in rules.get("placeholders", {}).items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["placeholder"] = placeholder

        # 4. Help text
        for field_name, text in rules.get("helptext", {}).items():
            if field_name in self.fields:
                self.fields[field_name].help_text = text


# ================================================================
# 🇧🇷 BRAZIL
# ================================================================

@register_company_form("BR")
class CompanyFormBR(CompanyForm):
    def clean_tax_id_1(self):
        cnpj = self.cleaned_data.get("tax_id_1")
        if not cnpj:
            return cnpj

        digits = "".join(d for d in cnpj if d.isdigit())
        if len(digits) != 14:
            raise forms.ValidationError("O CNPJ deve conter 14 dígitos.")
        return cnpj


# ================================================================
# 🇬🇧 UNITED KINGDOM
# ================================================================

@register_company_form("GB")
class CompanyFormGB(CompanyForm):
    def clean_tax_id_1(self):
        paye_office = self.cleaned_data.get("tax_id_1")
        if not paye_office:
            return paye_office

        digits = "".join(d for d in paye_office if d.isdigit())
        if len(digits) != 3:
            raise forms.ValidationError("PAYE Office has only 3 digitis")
        return paye_office
    

    def clean_tax_id_2(self):
        Reference_Number = self.cleaned_data.get("tax_id_2")
        if not Reference_Number:
            return Reference_Number

        digits = "".join(d for d in Reference_Number if d.isdigit())
        if len(digits) != 10:
            raise forms.ValidationError("Reference Number has only 10 digitis")
        return Reference_Number







# ================================================================
# 🇦🇷 ARGENTINA
# ================================================================

@register_company_form("AR")
class CompanyFormAR(CompanyForm):
    def clean_tax_id_1(self):
        cuit = self.cleaned_data.get("tax_id_1")
        if not cuit:
            return cuit

        digits = "".join(d for d in cuit if d.isdigit())
        if len(digits) != 11:
            raise forms.ValidationError("El CUIT debe tener 11 dígitos.")
        return cuit
