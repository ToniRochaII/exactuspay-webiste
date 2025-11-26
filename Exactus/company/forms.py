from django import forms
from Exactus.company.models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"
        exclude = ["country", "company_id"]
        widgets = {
            "account_status": forms.Select(attrs={"class": "form-select"}),
            "account_archive": forms.Select(attrs={"class": "form-select"}),
        }

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