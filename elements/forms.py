from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
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
