from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from django import forms
from django.core.exceptions import ValidationError


class ArgentinaEmployeeForm(BaseEmployeeForm):
    # Add Argentina-specific fields
    cuil = forms.CharField(
        max_length=13,
        required=True,
        label="CUIL",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "20-12345678-3",
            "data-mask": "00-00000000-0",
            "data-section": "personal"
        })
    )
    
    dni = forms.CharField(
        max_length=10,
        required=True,
        label="DNI",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "data-section": "personal"
        })
    )
    
    obra_social = forms.ChoiceField(
        choices=[('', 'Select...'), ('OSDE', 'OSDE'), ('GALENO', 'GALENO'), ('SWISS', 'Swiss Medical'), ('OTHER', 'Other')],
        required=False,
        label="Health Insurance",
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-section": "personal"
        })
    )
    
    sindicato = forms.CharField(
        max_length=100,
        required=False,
        label="Union",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "data-section": "job"
        })
    )

    class Meta(BaseEmployeeForm.Meta):
        labels = {
            **BaseEmployeeForm.Meta.labels,
            "employee_address_04": "Localidad",
            "employee_address_05": "Provincia",
            "employee_address_06": "Código Postal",
            "employee_address_07": "País",
            "bank_01": "Banco",
            "bank_02": "Titular de la Cuenta",
            "bank_03": "Número de Cuenta",
            "bank_04": "CBU",
            "department": "Departamento",
            "job_title": "Puesto",
        }
        
        exclude = BaseEmployeeForm.Meta.exclude + ['tax_info_01', 'tax_info_02']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['cuil'].initial = self.instance.tax_info_01
            self.fields['dni'].initial = self.instance.tax_info_02
    
    def clean_cuil(self):
        cuil = self.cleaned_data.get('cuil', '').replace('-', '')
        if not cuil or len(cuil) != 11:
            raise ValidationError("CUIL must be 11 digits (e.g., 20-12345678-3)")
        return cuil
    
    def clean_dni(self):
        dni = self.cleaned_data.get('dni', '')
        if not dni:
            raise ValidationError("DNI is required")
        return dni
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.tax_info_01 = self.cleaned_data.get('cuil', '')
        employee.tax_info_02 = self.cleaned_data.get('dni', '')
        if commit:
            employee.save()
        return employee