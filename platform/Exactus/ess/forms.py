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
    

from django import forms
from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from django.apps import apps

class EmployeeSelfServiceForm(BaseEmployeeForm):
    """
    A restricted form that ONLY validates/saves Address and Banking fields.
    This prevents 'This field is required' errors for Name/ID/Code.
    """
    class Meta(BaseEmployeeForm.Meta):
        # We inherit the model from the parent, but override the fields list
        fields = [
            # Address Fields
            'employee_address_type',
            'employee_address_01',
            'employee_address_02',
            'employee_address_03',
            'employee_address_04',
            'employee_address_05',
            'employee_address_06',
            
            # Bank Fields
            'bank_01',
            'bank_02',
            'bank_03',
            'bank_04',
            'bank_07',
            'bank_08'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Make sure these specific fields are required if they aren't already
        required_fields = ['employee_address_01', 'employee_address_03', 'employee_address_04', 'bank_01', 'bank_02', 'bank_04']
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True