# forms.py
from django import forms
from django.core.exceptions import ValidationError

class EmployeeDetailsForm(forms.Form):
    address = forms.CharField(max_length=255, required=True)
    bank_name = forms.CharField(max_length=100, required=True)
    bank_account = forms.CharField(max_length=50, required=True)
    
    def clean_bank_account(self):
        account = self.cleaned_data.get('bank_account')
        if not account.replace(' ', '').isdigit():
            raise ValidationError("Bank account must contain only numbers.")
        return account