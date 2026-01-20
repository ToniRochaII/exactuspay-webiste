from django import forms
from django.core.exceptions import ValidationError
import re

from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from Exactus.employee.models import Employee

class UnitedKingdomEmployeeForm(BaseEmployeeForm):
    """
    United Kingdom-specific Employee Form
    """

    # ==========================
    # UK-specific fields
    # ==========================
    # We map these to the 'tax' section
    
    national_insurance = forms.CharField(
        max_length=13,
        required=True,
        label="National Insurance Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "AB123456C",
            "data-section": "tax",
        }),
    )

    tax_code = forms.CharField(
        max_length=10,
        required=True,
        label="Tax Code",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "1257L",
            "data-section": "tax",
        }),
    )

    student_loan = forms.ChoiceField(
        choices=[
            ("", "Select..."),
            ("PLAN1", "Plan 1"),
            ("PLAN2", "Plan 2"),
            ("PLAN4", "Plan 4"),
            ("NONE", "None"),
        ],
        required=False,
        label="Student Loan Plan",
        widget=forms.Select(attrs={
            "class": "form-control", 
            "data-section": "tax"
        }),
    )

    pension_scheme = forms.ChoiceField(
        choices=[
            ("", "Select..."),
            ("AUTO", "Auto-enrolment"),
            ("NEST", "NEST"),
            ("OTHER", "Other"),
        ],
        required=False,
        label="Pension Scheme",
        widget=forms.Select(attrs={
            "class": "form-control", 
            "data-section": "tax"
        }),
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
            
            # Job / Payroll (Dates are here!)
            "employment_start_date", "employment_end_date",
            "department", "cost_centre", "job_title", "position_number", "fte",
            
            # Banking
            "bank_01", "bank_02", "bank_03", "bank_04", "bank_05",
            
            # Hidden Tax Fields
            "tax_info_01", "tax_info_02", "tax_info_03", "tax_info_04"
        ]

        labels = {
            **BaseEmployeeForm.Meta.labels,
            "employee_address_01": "Building and Street",
            "employee_address_03": "Town or City",
            "employee_address_04": "County",
            "employee_address_06": "Postcode",
            "bank_03": "Sort Code",
            "bank_04": "Account Number",
            "employment_start_date": "Start Date",
            "employment_end_date": "Termination Date",
        }

    # ==========================
    # Initialisation
    # ==========================

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Populate UK-specific fields when editing
        if self.instance and self.instance.pk:
            self.fields["national_insurance"].initial = self.instance.tax_info_01 or ""
            self.fields["tax_code"].initial = self.instance.tax_info_02 or ""
            # Note: You might want to map student loan/pension to tax_info_03/04 later

        # 2. Define Section Groupings (Exactly like Brazil)
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
                "national_insurance", "tax_code", "student_loan", "pension_scheme"
            ]
        }

        # 3. Apply 'data-section' attributes dynamically
        for section, fields in sections.items():
            for field_name in fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs["data-section"] = section
                    self.fields[field_name].widget.attrs.setdefault("class", "form-control")
                    self.fields[field_name].widget.attrs.setdefault("placeholder", " ")

        # 4. Specific configurations for Dates
        date_attrs = {
            "class": "form-control",
            "type": "date",              
            "data-section": "job", 
            "placeholder": " "
        }

        if "employment_start_date" in self.fields:
            self.fields["employment_start_date"].widget = forms.DateInput(attrs=date_attrs)
        
        if "employment_end_date" in self.fields:
            self.fields["employment_end_date"].widget = forms.DateInput(attrs=date_attrs)

        if "date_of_birth" in self.fields:
            self.fields["date_of_birth"].widget = forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
                "data-section": "personal"
            })

        # 5. Hide the generic tax_info fields
        for field_name in ("tax_info_01", "tax_info_02", "tax_info_03", "tax_info_04"):
            if field_name in self.fields:
                self.fields[field_name].widget = forms.HiddenInput()

    # ==========================
    # Validation
    # ==========================

    def clean_national_insurance(self):
        ni = self.cleaned_data.get("national_insurance", "").upper().replace(" ", "")
        pattern = r'^(?!BG|GB|KN|NK|NT|TN|ZZ)[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$'
        if not re.match(pattern, ni):
            raise ValidationError("Invalid National Insurance Number")
        return ni

    def clean_tax_code(self):
        code = self.cleaned_data.get("tax_code", "").upper().strip()
        if not code:
            raise ValidationError("Tax Code is required")
        return code
    
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
        
        # Save custom UK fields to generic slots
        employee.tax_info_01 = self.cleaned_data.get("national_insurance", "")
        employee.tax_info_02 = self.cleaned_data.get("tax_code", "")
        # You can save student_loan/pension to tax_info_03/04 if needed
        
        if commit:
            employee.save()
        return employee