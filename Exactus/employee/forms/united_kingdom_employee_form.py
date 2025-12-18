from django import forms
from django.core.exceptions import ValidationError
import re

from Exactus.employee.forms.base_employee_form import BaseEmployeeForm


class UnitedKingdomEmployeeForm(BaseEmployeeForm):

    national_insurance = forms.CharField(
        max_length=13,
        required=True,
        label="National Insurance Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "AB123456C",
                "data-section": "personal",
            }
        ),
    )

    tax_code = forms.CharField(
        max_length=10,
        required=True,
        label="Tax Code",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "1257L",
                "data-section": "personal",
            }
        ),
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
        widget=forms.Select(
            attrs={"class": "form-control", "data-section": "tax"}
        ),
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
        widget=forms.Select(
            attrs={"class": "form-control", "data-section": "tax"}
        ),
    )

    class Meta(BaseEmployeeForm.Meta):
        labels = {
            **BaseEmployeeForm.Meta.labels,
            "employee_address_01": "Building and Street",
            "employee_address_03": "Town or City",
            "employee_address_04": "County",
            "employee_address_06": "Postcode",
            "bank_03": "Sort Code",
            "bank_04": "Account Number",
        }
        widgets = {
            **BaseEmployeeForm.Meta.widgets,
        }
        exclude = BaseEmployeeForm.Meta.exclude

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["national_insurance"].initial = self.instance.tax_info_01 or ""
            self.fields["tax_code"].initial = self.instance.tax_info_02 or ""

        for f in ("tax_info_01", "tax_info_02"):
            if f in self.fields:
                self.fields[f].widget = forms.HiddenInput()

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

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.tax_info_01 = self.cleaned_data["national_insurance"]
        employee.tax_info_02 = self.cleaned_data["tax_code"]
        if commit:
            employee.save()
        return employee
