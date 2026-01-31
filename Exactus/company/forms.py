from django import forms
from Exactus.company.models import Company, ClientGroup

# -------------------------------------------------------------------------
# UPLOAD FORM
# -------------------------------------------------------------------------
class CompanyUploadForm(forms.Form):
    # FIXED: Renamed from 'file' to 'csv_file' to match the template
    csv_file = forms.FileField(  
        label="CSV File",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
        required=True
    )
    
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run (Test without saving)",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Check this box to validate the CSV data without saving changes to the database."
    )

# -------------------------------------------------------------------------
# STANDARD FORMS
# -------------------------------------------------------------------------
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"
        widgets = {
            'country': forms.HiddenInput(),
        }

class ClientGroupForm(forms.ModelForm):
    class Meta:
        model = ClientGroup
        fields = ["name", "description"]