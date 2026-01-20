from django import forms
from django.core.exceptions import ValidationError
import re

from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from Exactus.employee.models import Employee

class BrazilEmployeeForm(BaseEmployeeForm):
    """
    Brazil-specific Employee Form
    """

    # ==========================
    # Brazil-specific fields
    # ==========================
    # We map these to the 'tax' section so the "Taxation Details" tab isn't empty.
    # If you prefer them in Personal, change data-section to "personal".
    
    cpf = forms.CharField(
        max_length=14,
        required=True,
        label="CPF",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.000.000-00",
            "data-mask": "000.000.000-00",
            "data-section": "tax", 
        }),
        help_text="Brazilian individual taxpayer registry (CPF)",
    )

    pis = forms.CharField(
        max_length=14,
        required=True,
        label="PIS / PASEP",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.00000.00-0",
            "data-mask": "000.00000.00-0",
            "data-section": "tax",
        }),
        help_text="Brazilian social integration program number",
    )

    ctps_number = forms.CharField(
        max_length=20,
        required=False,
        label="CTPS Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "data-section": "tax",
        }),
        help_text="Brazilian work permit number (CTPS)",
    )

    # ==========================
    # Meta configuration
    # ==========================

    class Meta(BaseEmployeeForm.Meta):
        model = Employee
        
        fields = [
            # Standard Fields
            "employee_id", "employee_number", "employee_code", 
            "employee_name", "employee_surname", "gender", "date_of_birth", 
            "marital_status", 
            
            # Address
            "employee_address_type", "employee_address_01", "employee_address_02",
            "employee_address_03", "employee_address_04", "employee_address_05",
            "employee_address_06", "employee_address_07",
            
            # Job / Payroll
            "employment_start_date", "employment_end_date",
            "department", "cost_centre", "job_title", "position_number", "fte",
            
            # Banking
            "bank_01", "bank_02", "bank_03", "bank_04", "bank_05",
            
            # Hidden Tax Fields (Mapped manually in save/init)
            "tax_info_01", "tax_info_02", "tax_info_03", "tax_info_04",
            "tax_info_05", "tax_info_06", "tax_info_07"
        ]

        exclude = [] 

        labels = {
            **BaseEmployeeForm.Meta.labels,
            "tax_info_01": "CPF",
            "tax_info_02": "PIS / PASEP",
            "tax_info_03": "CTPS",
            "employment_start_date": "Start Date",
            "employment_end_date": "Termination Date",
        }

    # ==========================
    # Initialisation
    # ==========================

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Populate Brazil-specific fields when editing
        if self.instance and self.instance.pk:
            self.fields["cpf"].initial = self.instance.tax_info_01 or ""
            self.fields["pis"].initial = self.instance.tax_info_02 or ""
            self.fields["ctps_number"].initial = self.instance.tax_info_03 or ""

        # 2. Define Section Groupings
        # These keys MUST match the tabs in your HTML: 
        # personal, address, bank, job, tax, pay
        
        sections = {
            "personal": [
                "employee_id", "employee_number", "employee_code", 
                "employee_name", "employee_surname", "gender", 
                "date_of_birth", "marital_status"
            ],
            "address": [
                "employee_address_type", "employee_address_01", "employee_address_02",
                "employee_address_03", "employee_address_04", "employee_address_05",
                "employee_address_06", "employee_address_07"
            ],
            "bank": [
                "bank_01", "bank_02", "bank_03", "bank_04", "bank_05"
            ],
            "job": [
                "employment_start_date", "employment_end_date",
                "department", "cost_centre", "job_title", 
                "position_number", "fte"
            ],
            "tax": [
                "cpf", "pis", "ctps_number" # Custom fields
            ]
        }

        # 3. Apply 'data-section' attributes dynamically
        for section, fields in sections.items():
            for field_name in fields:
                if field_name in self.fields:
                    # Update widget attributes without overwriting existing ones
                    self.fields[field_name].widget.attrs["data-section"] = section
                    self.fields[field_name].widget.attrs.setdefault("class", "form-control")
                    self.fields[field_name].widget.attrs.setdefault("placeholder", " ")

        # 4. Specific configurations for Dates
        # Ensures they use the HTML5 date picker and are strictly in the 'job' section
        date_attrs = {
            "class": "form-control",
            "type": "date",              
            "data-section": "job", # Matches HTML filter: field|in_section:"job"
            "placeholder": " "
        }

        if "employment_start_date" in self.fields:
            self.fields["employment_start_date"].widget = forms.DateInput(attrs=date_attrs)
            self.fields["employment_start_date"].label = "Start Date"
        
        if "employment_end_date" in self.fields:
            self.fields["employment_end_date"].widget = forms.DateInput(attrs=date_attrs)
            self.fields["employment_end_date"].label = "Termination Date (Leave empty if active)"

        if "date_of_birth" in self.fields:
            self.fields["date_of_birth"].widget = forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
                "data-section": "personal"
            })

        # 5. Hide the generic tax_info fields (since we mapped them to custom fields)
        for field_name in ("tax_info_01", "tax_info_02", "tax_info_03"):
            if field_name in self.fields:
                self.fields[field_name].widget = forms.HiddenInput()

    # ==========================
    # Validation
    # ==========================

    def clean_cpf(self):
        raw_cpf = self.cleaned_data.get("cpf", "")
        cpf = re.sub(r"\D", "", raw_cpf)
        if len(cpf) != 11:
            raise ValidationError("CPF must contain exactly 11 digits")
        return cpf

    def clean_pis(self):
        raw_pis = self.cleaned_data.get("pis", "")
        pis = re.sub(r"\D", "", raw_pis)
        if len(pis) != 11:
            raise ValidationError("PIS/PASEP must contain exactly 11 digits")
        return pis
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("employment_start_date")
        end = cleaned_data.get("employment_end_date")

        if start and end and end < start:
            self.add_error("employment_end_date", "Termination date cannot be before Start date.")
        
        return cleaned_data

    # ==========================
    # Persistence
    # ==========================

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.tax_info_01 = self.cleaned_data.get("cpf", "")
        employee.tax_info_02 = self.cleaned_data.get("pis", "")
        employee.tax_info_03 = self.cleaned_data.get("ctps_number", "")

        if commit:
            employee.save()
        return employee