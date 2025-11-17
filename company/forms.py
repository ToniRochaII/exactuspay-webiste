from django import forms
from company.models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"
        exclude = ["country", "company_id"]
