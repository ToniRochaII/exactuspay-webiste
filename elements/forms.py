# elements/forms.py
from django import forms
from .models import Element

class ElementForm(forms.ModelForm):
    class Meta:
        model = Element
        exclude = ["country"]
        widgets = {
            "element_status": forms.Select(attrs={"class": "form-select"}),
            "element_frequency": forms.Select(attrs={"class": "form-select"}),
            "element_type": forms.Select(attrs={"class": "form-select"}),
            "element_class": forms.Select(attrs={"class": "form-select"}),
            "element_category": forms.Select(attrs={"class": "form-select"}),
            "element_categorytype": forms.Select(attrs={"class": "form-select"}),
        }

class ElementUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with payroll elements data"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database"
    )