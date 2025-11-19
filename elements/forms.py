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
