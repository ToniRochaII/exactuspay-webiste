from django import forms
from .models import PDcode
from company.models import Company
from country.models import Country


class PDcodeForm(forms.ModelForm):
    """
    Form for creating/updating PD codes.
    - Excludes company (set in the view)
    - Validates that pdcode_code is unique per company
    """

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = PDcode
        exclude = ["company", "slug"]
        widgets = {
            "pdcode_status": forms.Select(attrs={"class": "form-select"}),
            "pdcode_frequency": forms.Select(attrs={"class": "form-select"}),
            "pdcode_type": forms.Select(attrs={"class": "form-select"}),
            "pdcode_class": forms.Select(attrs={"class": "form-select"}),
            "pdcode_category": forms.Select(attrs={"class": "form-select"}),
            "pdcode_categorytype": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_pdcode_code(self):
        code = self.cleaned_data.get("pdcode_code")

        # No company passed → skip custom validation (shouldn't happen in our views)
        if not self.company or not code:
            return code

        qs = PDcode.objects.filter(company=self.company, pdcode_code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "This PD Code already exists for this company."
            )

        return code


# pdcodes/forms.py - Update the PDcodeCountryUploadForm
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