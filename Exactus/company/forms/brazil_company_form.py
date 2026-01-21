from django import forms
from django.core.exceptions import ValidationError
from Exactus.company.forms.base_company_form import BaseCompanyForm
import re

class BrazilCompanyForm(BaseCompanyForm):
    """
    Brazil Specific Company Form.
    Strictly mapped to the 'BR Company Form' visual specification.
    """

    # ──────────────────────────────────────────────────────────────
    # TAB: TAXATION (Employer Settings)
    # ──────────────────────────────────────────────────────────────
    
    # [Block: Employer Settings]
    cnpj = forms.CharField(
        label="CNPJ",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "00.000.000/0001-00",
            "data-mask": "00.000.000/0001-00",
            "data-section": "tax"
        })
    )

    registration_date = forms.DateField(
        label="Registration Date",
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "data-section": "tax"
        })
    )

    primary_cnae = forms.CharField(
        label="Primary Economical Registration Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    secondary_cnae = forms.CharField(
        label="Secondary Economical Registration",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    business_type_code = forms.CharField(
        label="Business Type Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # ──────────────────────────────────────────────────────────────
    # TAB: RTI SETTINGS (Agent Address)
    # ──────────────────────────────────────────────────────────────
    
    # These fields exist in BaseCompanyForm, but we explicitly label and section them here
    agent_full_name = forms.CharField(
        label="Contact Full Name",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}) 
        # Note: We map RTI/Agent to 'tax' section in the HTML tabs logic
    )
    agent_road_name_1 = forms.CharField(
        label="Road Name",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_road_name_2 = forms.CharField(
        label="Road Name line 2",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_town = forms.CharField(
        label="Town",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_post_code = forms.CharField(
        label="Post Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    class Meta(BaseCompanyForm.Meta):
        labels = {
            **BaseCompanyForm.Meta.labels,
            
            # [Tab: Company] Business Details
            "company_code": "Company Code",
            "company_number": "Company Number",
            "trade_name": "Business Trade Name",
            "legal_name": "Legal Trade Name",

            # [Tab: Communication] Business Details
            "contact": "Contact",
            "phone": "Telephone",
            "email": "eMail",
            "website": "website",

            # [Tab: Communication] Business Address
            "building_name": "Building Name",
            "road_name_1": "Road Name",
            "road_name_2": "Road Name line 2",
            "town": "Town",
            "post_code": "Post Code",
            "county": "County",
        }

        widgets = {
            **BaseCompanyForm.Meta.widgets,
            
            # --- TAB: COMPANY ---
            "company_code": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "company_number": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),

            # --- TAB: COMMUNICATION ---
            "contact": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "data-section": "communication"}),
            "website": forms.URLInput(attrs={"class": "form-control", "data-section": "communication"}),
            
            # Address Block
            "building_name": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "road_name_1": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "road_name_2": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "town": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "post_code": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "county": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Map Tax Data (01-05)
            self.fields["cnpj"].initial = self.instance.tax_id_01 or ""
            self.fields["registration_date"].initial = self.instance.tax_id_02 or ""
            self.fields["primary_cnae"].initial = self.instance.tax_id_03 or ""
            self.fields["secondary_cnae"].initial = self.instance.tax_id_04 or ""
            self.fields["business_type_code"].initial = self.instance.tax_id_05 or ""

        # Hide generic slots to avoid duplicates
        hidden_prefixes = ("tax_id_", "bank_")
        for name, field in self.fields.items():
            if name.startswith(hidden_prefixes):
                field.widget = forms.HiddenInput()

    def clean_cnpj(self):
        # Basic validation to ensure numbers only if strictly required
        raw_cnpj = self.cleaned_data.get("cnpj", "")
        # Remove non-digits
        cnpj = re.sub(r"\D", "", raw_cnpj)
        # Brazil CNPJ is 14 digits
        if len(cnpj) != 14:
            raise ValidationError("CNPJ must be exactly 14 digits.")
        return raw_cnpj # Return raw to preserve formatting if desired

    def save(self, commit=True):
        company = super().save(commit=False)
        
        # Save Tax Data (01-05)
        company.tax_id_01 = self.cleaned_data.get("cnpj", "")
        company.tax_id_02 = self.cleaned_data.get("registration_date", "")
        company.tax_id_03 = self.cleaned_data.get("primary_cnae", "")
        company.tax_id_04 = self.cleaned_data.get("secondary_cnae", "")
        company.tax_id_05 = self.cleaned_data.get("business_type_code", "")

        if commit:
            company.save()
        return company