from django import forms
from .models import PDcode


class PDcodeForm(forms.ModelForm):
    class Meta:
        model = PDcode
        exclude = ["company"]
        widgets = {
            "pdcode_status": forms.Select(attrs={"class": "form-select"}),
            "pdcode_frequency": forms.Select(attrs={"class": "form-select"}),
            "pdcode_type": forms.Select(attrs={"class": "form-select"}),
            "pdcode_class": forms.Select(attrs={"class": "form-select"}),
            "pdcode_category": forms.Select(attrs={"class": "form-select"}),
            "pdcode_categorytype": forms.Select(attrs={"class": "form-select"}),
        }
