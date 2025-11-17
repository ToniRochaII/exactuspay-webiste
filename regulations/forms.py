from django import forms
from .models import Regulations

class RegulationsForm(forms.ModelForm):
    class Meta:
        model = Regulations
        fields = ["fiscal_year", "effective_date"]
        widgets = {"effective_date": forms.DateInput(attrs={"type": "date", "class": "form-control"})}
        exclude = ["country"]