# employee/forms.py
from django import forms
from django.core.exceptions import ValidationError
from Exactus.employee.models import Employee


class BaseEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ["company"]

        labels = {
            "employee_id": "Employee ID",
            "employee_number": "Employee Number",
            "employee_code": "Employee Code",
            "employee_name": "First Name",
            "employee_surname": "Last Name",
            "gender": "Gender",
            "date_of_birth": "Date of Birth",
            "marital_status": "Marital Status",
            "employee_address_type": "Address Type",
            "employee_address_01": "Address Line 1",
            "employee_address_02": "Address Line 2",
            "employee_address_03": "Address Line 3",
            "employee_address_04": "City",
            "employee_address_05": "State/Province",
            "employee_address_06": "Postal Code",
            "employee_address_07": "Country",
            "bank_01": "Bank Name",
            "bank_02": "Account Holder Name",
            "bank_03": "Account Number",
            "bank_04": "Bank Code",
            "bank_05": "Branch Code",
            "bank_06": "Account Type",
            "bank_07": "IBAN",
            "bank_08": "SWIFT/BIC",
            "bank_09": "Currency",
            "bank_10": "Payment Method",
            "department": "Department",
            "cost_centre": "Cost Centre",
            "job_title": "Job Title",
            "position_number": "Position Number",
            "fte": "Full-Time Equivalent",
            "tax_info_01": "Tax ID",
            "tax_info_02": "Tax Status",
            "tax_info_03": "Exemption Amount",
            "tax_info_04": "Tax Bracket",
            "tax_info_05": "Tax Residency",
            "tax_info_06": "Additional Withholding",
            "tax_info_07": "Tax Notes",
        }

        widgets = {
            # Personal Information
            "employee_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "personal"  # Make sure this is included
            }),
            "employee_number": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "personal"
            }),
            "employee_code": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "personal"
            }),
            "employee_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "personal"
            }),
            "employee_surname": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "personal"
            }),
            "gender": forms.Select(attrs={
                "class": "form-control",
                "data-section": "personal"
            }),
            "marital_status": forms.Select(attrs={
                "class": "form-control",
                "data-section": "personal"
            }),
            "employee_address_type": forms.Select(attrs={
                "class": "form-control",
                "data-section": "address"
            }),
            "date_of_birth": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": " ",
                "data-section": "personal"
            }),

            # Address Information
            "employee_address_01": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"  # Make sure this is included
            }),
            "employee_address_02": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"
            }),
            "employee_address_03": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"
            }),
            "employee_address_04": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"
            }),
            "employee_address_05": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"
            }),
            "employee_address_06": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"
            }),
            "employee_address_07": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "address"
            }),

            # Bank Information
            "bank_01": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_02": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_03": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_04": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_05": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_06": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_07": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_08": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_09": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),
            "bank_10": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "bank"
            }),

            # Job Information
            "department": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "job"
            }),
            "cost_centre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "job"
            }),
            "job_title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "job"
            }),
            "position_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "job"
            }),
            "fte": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.1",
                "placeholder": " ",
                "data-section": "job"
            }),

            # Tax Information
            "tax_info_01": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "tax"
            }),
            "tax_info_02": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "tax"
            }),
            "tax_info_03": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "tax"
            }),
            "tax_info_04": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "tax"
            }),
            "tax_info_05": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "tax"
            }),
            "tax_info_06": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": " ",
                "data-section": "tax"
            }),
            "tax_info_07": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": " ",
                "data-section": "tax"
            }),
        }

    # Cleaning methods
    def clean_employee_id(self):
        eid = self.cleaned_data.get("employee_id", "").strip()
        if not eid:
            raise ValidationError("Employee ID cannot be empty.")
        return eid

    def clean_employee_name(self):
        name = self.cleaned_data.get("employee_name", "").strip()
        if len(name) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        return name

    def clean_employee_surname(self):
        surname = self.cleaned_data.get("employee_surname", "").strip()
        if len(surname) < 2:
            raise ValidationError("Last name must be at least 2 characters.")
        return surname

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if not dob:
            raise ValidationError("Date of birth is required.")
        return dob



class EmployeeUploadForm(forms.Form):
    file = forms.FileField()
    dry_run = forms.BooleanField(required=False)
