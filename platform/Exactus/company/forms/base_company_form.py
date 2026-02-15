from django import forms
from django.core.exceptions import ValidationError
from Exactus.company.models import Company

class BaseCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ["country"]  # Handled in the view

        labels = {
            # Identification
            "company_code": "Company Code",
            "trade_name": "Trade Name",
            "legal_name": "Legal Name",
            "company_number": "Registration Number",
            "logo": "Company Logo",

            # Communication
            "contact": "Primary Contact Name",
            "phone": "Telephone",
            "email": "Email Address",
            "website": "Website URL",
            
            # Address
            "building_name": "Building Name / Number",
            "road_name_1": "Street Address 1",
            "road_name_2": "Street Address 2",
            "town": "Town / City",
            "county": "County / State",
            "post_code": "Post / Zip Code",

            # RTI / Auth / Agent
            "rti_user_id": "RTI / API User ID",
            "rti_password": "RTI / API Password",
            "agent_full_name": "Agent Contact Name",
            "agent_road_name_1": "Agent Street Address 1",
            "agent_road_name_2": "Agent Street Address 2",
            "agent_town": "Agent Town / City",
            "agent_post_code": "Agent Post Code",
        }

        widgets = {
            # ─── DETAILS SECTION ───
            "company_code": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "company_number": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "logo": forms.FileInput(attrs={"class": "form-control", "data-section": "details"}),

            # ─── COMMUNICATION SECTION ───
            "contact": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "data-section": "communication"}),
            "website": forms.URLInput(attrs={"class": "form-control", "data-section": "communication"}),

            # ─── ADDRESS SECTION ───
            "building_name": forms.TextInput(attrs={"class": "form-control", "data-section": "address"}),
            "road_name_1": forms.TextInput(attrs={"class": "form-control", "data-section": "address"}),
            "road_name_2": forms.TextInput(attrs={"class": "form-control", "data-section": "address"}),
            "town": forms.TextInput(attrs={"class": "form-control", "data-section": "address"}),
            "county": forms.TextInput(attrs={"class": "form-control", "data-section": "address"}),
            "post_code": forms.TextInput(attrs={"class": "form-control", "data-section": "address"}),

            # ─── TAX / RTI / AGENT SECTION ───
            "rti_user_id": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),
            "rti_password": forms.PasswordInput(attrs={"class": "form-control", "data-section": "tax", "autocomplete": "new-password"}),
            
            # Agent Details (Grouped under Tax/RTI usually)
            "agent_full_name": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),
            "agent_road_name_1": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),
            "agent_road_name_2": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),
            "agent_town": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),
            "agent_post_code": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),

            # Generic Tax IDs (Hidden by default, exposed by subclasses)
            "tax_id_01": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_02": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_03": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_04": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_05": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_06": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_07": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_08": forms.Select(attrs={"class": "form-select", "data-section": "settings"}),
            "tax_id_09": forms.Select(attrs={"class": "form-select", "data-section": "settings"}),
            "tax_id_10": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_11": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_12": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_13": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_14": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_15": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_16": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_17": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_18": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_19": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            "tax_id_20": forms.TextInput(attrs={"class": "form-control", "data-section": "Tax"}),
            

            # ─── BANK SECTION ───
            # We provide widgets for all 20, though most will be unused in Base.
            # Subclasses will label them specific to the country.
            "bank_01": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_02": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_03": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_04": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_05": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_06": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_07": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_08": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_09": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_10": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_11": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_12": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_13": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_14": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_15": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_16": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_17": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_18": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_19": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            "bank_20": forms.TextInput(attrs={"class": "form-control", "data-section": "bank"}),
            
            # ─── SETTINGS SECTION ───
            "account_status": forms.Select(attrs={"class": "form-select", "data-section": "settings"}),
            "account_archive": forms.Select(attrs={"class": "form-select", "data-section": "settings"}),
        }

    def __init__(self, *args, **kwargs):
        # Remove 'country' from kwargs if it was passed by legacy views
        if 'country' in kwargs:
            kwargs.pop('country')
        super().__init__(*args, **kwargs)

    def clean_company_code(self):
        code = self.cleaned_data.get("company_code", "").upper().strip()
        if not code:
            raise ValidationError("Company Code is required.")
        return code