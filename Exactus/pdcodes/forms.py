from django import forms
from Exactus.pdcodes.models import PDcode
from Exactus.company.models import Company
from Exactus.country.models import Country


# Exactus/pdcodes/forms.py
from django import forms
from Exactus.pdcodes.models import PDcode
from Exactus.elements.models import Element

class PDcodeForm(forms.ModelForm):
    # We explicitly define the field to use checkboxes
    applicable_bases = forms.ModelMultipleChoiceField(
        queryset=Element.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Applicable Bases"
    )

    class Meta:
        model = PDcode
        fields = [
            'pdcode_code', 'pdcode_name', 'pdcode_description',
            'pdcode_status', 'pdcode_frequency', 'pdcode_type',
            'pdcode_class', 'pdcode_category', 'pdcode_categorytype',
            'pdcode_account', 'pdcode_map_code', 'pdcode_gl_account',
            # Boolean Flags

            # New Field
            'applicable_bases'
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

            "applicable_bases": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),

        }
    def __init__(self, *args, **kwargs):
        # We expect 'company' to be passed in kwargs from the view
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if self.company:
            # Filter elements:
            # 1. Must belong to the same country as the company
            # 2. Must be a "Base" category (as per your requirement)
            self.fields['applicable_bases'].queryset = Element.objects.filter(
                country=self.company.country,
                element_categorytype='Base'
            )





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