from django import forms
from Exactus.pdcodes.models import PDcode
from Exactus.company.models import Company
from Exactus.country.models import Country


# pdcodes/forms.py
class PDcodeForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = PDcode
        fields = [
            "pdcode_code",
            "pdcode_name",
            "pdcode_description",
            "pdcode_status",
            "pdcode_frequency",
            "pdcode_type",
            "pdcode_class",
            "pdcode_category",
            "pdcode_categorytype",
            "pdcode_account",
            "pdcode_map_code",
            "pdcode_gl_account",
            "pdcode_taxable",
            "pdcode_tax_flat",
            "pdcode_tax_irregular",
            "pdcode_social_securitable",
            "pdcode_pensionable",
            "pdcode_payable",
            "pdcode_calculate",
        ]

        widgets = {
            "pdcode_code": forms.TextInput(attrs={"class": "form-control"}),
            "pdcode_name": forms.TextInput(attrs={"class": "form-control"}),
            "pdcode_description": forms.TextInput(attrs={"class": "form-control"}),

            "pdcode_status": forms.Select(attrs={"class": "form-select"}),
            "pdcode_frequency": forms.Select(attrs={"class": "form-select"}),
            "pdcode_type": forms.Select(attrs={"class": "form-select"}),
            "pdcode_class": forms.Select(attrs={"class": "form-select"}),
            "pdcode_category": forms.Select(attrs={"class": "form-select"}),
            "pdcode_categorytype": forms.Select(attrs={"class": "form-select"}),

            "pdcode_account": forms.TextInput(attrs={"class": "form-control"}),
            "pdcode_map_code": forms.TextInput(attrs={"class": "form-control"}),
            "pdcode_gl_account": forms.TextInput(attrs={"class": "form-control"}),

            "pdcode_taxable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pdcode_tax_flat": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pdcode_tax_irregular": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pdcode_social_securitable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pdcode_pensionable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pdcode_payable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "pdcode_calculate": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }






# pdcodes/forms.py - Update the PDcodeUploadForm
class PDcodeUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with PD code data - will be applied to ALL companies in this country"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database"
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label="Update Existing",
        help_text="Update existing PD codes if found in each company"
    )
    company_filter = forms.MultipleChoiceField(
        required=False,
        label="Filter Companies",
        help_text="Select specific companies to apply to (leave empty for all companies)",
        widget=forms.CheckboxSelectMultiple,
        choices=[]  # Will be populated in __init__
    )
    
    def __init__(self, *args, **kwargs):
        self.country = kwargs.pop('country', None)
        super().__init__(*args, **kwargs)
        
        if self.country:
            # Remove is_active filter
            companies = Company.objects.filter(country=self.country)
            company_choices = [(c.company_id, f"{c.trade_name} ({c.company_code})") for c in companies]
            self.fields['company_filter'].choices = company_choices

# pdcodes/forms.py - Add this form
class PDcodeCountryUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with PD code data - will be applied to ALL companies in this country"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database"
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label="Update Existing",
        help_text="Update existing PD codes if found in each company"
    )
    company_filter = forms.MultipleChoiceField(
        required=False,
        label="Filter Companies",
        help_text="Select specific companies to apply to (leave empty for all companies)",
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        self.country = kwargs.pop('country', None)
        super().__init__(*args, **kwargs)
        
        if self.country:
            companies = Company.objects.filter(country=self.country, is_active=True)
            company_choices = [(c.company_id, f"{c.trade_name} ({c.company_code})") for c in companies]
            self.fields['company_filter'].choices = company_choices