from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from django import forms
from django.core.exceptions import ValidationError
import re


class UnitedKingdomEmployeeForm(BaseEmployeeForm):
    # Add UK-specific fields
    national_insurance = forms.CharField(
        max_length=13,
        required=True,
        label="National Insurance Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "AB123456C",
            "data-section": "personal"
        })
    )
    
    tax_code = forms.CharField(
        max_length=10,
        required=True,
        label="Tax Code",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "1257L",
            "data-section": "personal"
        })
    )
    
    student_loan = forms.ChoiceField(
        choices=[('', 'Select...'), ('PLAN1', 'Plan 1'), ('PLAN2', 'Plan 2'), ('PLAN4', 'Plan 4'), ('NONE', 'None')],
        required=False,
        label="Student Loan Plan",
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-section": "tax"
        })
    )
    
    pension_scheme = forms.ChoiceField(
        choices=[('', 'Select...'), ('AUTO', 'Auto-enrolment'), ('NEST', 'NEST'), ('OTHER', 'Other')],
        required=False,
        label="Pension Scheme",
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-section": "tax"
        })
    )

    class Meta(BaseEmployeeForm.Meta):
        labels = {
            **BaseEmployeeForm.Meta.labels,
            "employee_address_01": "Building and Street",
            "employee_address_02": "Address Line 2",
            "employee_address_03": "Town or City",
            "employee_address_04": "County",
            "employee_address_06": "Postcode",
            "bank_01": "Bank Name",
            "bank_02": "Account Holder Name",
            "bank_03": "Sort Code",
            "bank_04": "Account Number",
        }
        
        exclude = BaseEmployeeForm.Meta.exclude + ['tax_info_01', 'tax_info_02']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UK-specific field ordering
        if self.instance and self.instance.pk:
            self.fields['national_insurance'].initial = self.instance.tax_info_01
            self.fields['tax_code'].initial = self.instance.tax_info_02
    
    def clean_national_insurance(self):
        ni = self.cleaned_data.get('national_insurance', '').upper().replace(' ', '')
        if not ni:
            raise ValidationError("National Insurance Number is required")
        
        # Basic NI validation pattern
        ni_pattern = r'^[A-Z]{2}[0-9]{6}[A-Z]$'
        if not re.match(ni_pattern, ni):
            raise ValidationError("Invalid National Insurance Number format (e.g., AB123456C)")
        return ni
    
    def clean_tax_code(self):
        tax_code = self.cleaned_data.get('tax_code', '').upper()
        if not tax_code:
            raise ValidationError("Tax Code is required")
        return tax_code
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.tax_info_01 = self.cleaned_data.get('national_insurance', '')
        employee.tax_info_02 = self.cleaned_data.get('tax_code', '')
        if commit:
            employee.save()
        return employee