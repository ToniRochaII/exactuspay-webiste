from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from django import forms
from django.core.exceptions import ValidationError
import re


class BrazilEmployeeForm(BaseEmployeeForm):
    # Add Brazil-specific fields
    cpf = forms.CharField(
        max_length=14,
        required=True,
        label="CPF",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.000.000-00",
            "data-mask": "000.000.000-00",
            "data-section": "personal"
        })
    )
    
    pis = forms.CharField(
        max_length=14,
        required=True,
        label="PIS/PASEP",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.00000.00-0",
            "data-mask": "000.00000.00-0",
            "data-section": "personal"
        })
    )
    
    ctps_number = forms.CharField(
        max_length=20,
        required=False,
        label="CTPS Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "data-section": "personal"
        })
    )

    class Meta(BaseEmployeeForm.Meta):
        # Override labels for tax_info fields
        labels = {
            **BaseEmployeeForm.Meta.labels,
            "tax_info_01": "RG (Identity Card)",
            "tax_info_02": "Voter ID",
            "tax_info_03": "Work Permit",
        }
        
        # FIX: Don't exclude tax_info fields - they're needed for saving
        # Remove this line:
        # exclude = BaseEmployeeForm.Meta.exclude + ['tax_info_01', 'tax_info_02', 'tax_info_03']
        
        # Instead, just use the base exclude
        exclude = BaseEmployeeForm.Meta.exclude

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from tax_info fields if editing existing employee
        if self.instance and self.instance.pk:
            self.fields['cpf'].initial = self.instance.tax_info_01
            self.fields['pis'].initial = self.instance.tax_info_02
        
        # Hide the original tax_info fields since we're using Brazil-specific ones
        self.fields['tax_info_01'].widget = forms.HiddenInput()
        self.fields['tax_info_02'].widget = forms.HiddenInput()
        self.fields['tax_info_03'].widget = forms.HiddenInput()
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '').replace('.', '').replace('-', '')
        if not cpf or len(cpf) != 11:
            raise ValidationError("CPF must be 11 digits (e.g., 123.456.789-09)")
        return cpf
    
    def clean_pis(self):
        pis = self.cleaned_data.get('pis', '').replace('.', '').replace('-', '')
        if not pis or len(pis) != 11:
            raise ValidationError("PIS/PASEP must be 11 digits (e.g., 123.45678.90-1)")
        return pis
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        # Map Brazil-specific fields to tax_info fields
        employee.tax_info_01 = self.cleaned_data.get('cpf', '')
        employee.tax_info_02 = self.cleaned_data.get('pis', '')
        if commit:
            employee.save()
        return employee
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        # Map Brazil-specific fields - these will be saved separately
        # since tax_info fields are excluded
        cpf_value = self.cleaned_data.get('cpf', '')
        pis_value = self.cleaned_data.get('pis', '')
        
        if commit:
            employee.save()
            # Update the tax_info fields after saving
            employee.tax_info_01 = cpf_value
            employee.tax_info_02 = pis_value
            employee.save(update_fields=['tax_info_01', 'tax_info_02'])
        
        return employee
    

