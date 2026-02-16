from django import forms

class CompanyUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file containing company data."
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=True,
        label="Dry Run (Validate only)",
        help_text="If checked, the system will validate the data without saving it."
    )
