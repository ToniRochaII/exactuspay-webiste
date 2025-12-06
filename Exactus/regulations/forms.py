# regulations/forms.py
from django import forms
from Exactus.regulations.models import Regulations

class RegulationsForm(forms.ModelForm):
    class Meta:
        model = Regulations
        fields = [
            "country",
            "fiscal_year",
            "effective_date",
        ]
        widgets = {
            "effective_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fiscal_year": forms.NumberInput(attrs={"class": "form-control"}),
        }
        exclude = ["country"]

class RegulationsUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with regulations data"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database"
    )
    