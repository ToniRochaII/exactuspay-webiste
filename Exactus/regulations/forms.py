# regulations/forms.py
from django import forms
from Exactus.regulations.models import Regulations

class RegulationsForm(forms.ModelForm):
    class Meta:
        model = Regulations
        fields = [
            "fiscal_year",
            "effective_date",
            # Add other fields here as needed (e.g. name, description)
            # Do NOT include 'country' here if you are excluding it below
        ]
        widgets = {
            "effective_date": forms.DateInput(
                format='%Y-%m-%d',  # <--- CRITICAL: Forces YYYY-MM-DD for the input value
                attrs={
                    "type": "date", 
                    "class": "form-control",
                    "placeholder": "Select Date" # <--- CRITICAL: Required for Floating Labels
                }
            ),
            "fiscal_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "YYYY"
                }
            ),
        }
        exclude = ["country"]

class RegulationsUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with regulations data",
        widget=forms.FileInput(attrs={"class": "form-control"}) # Added styling here too
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}) # Standard Bootstrap checkbox
    )