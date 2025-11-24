# employee/forms.py
from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ["company"]
        widgets = {
            "employee_id": forms.TextInput(attrs={"class": "form-control"}),
            "employee_number": forms.NumberInput(attrs={"class": "form-control"}),
            "employee_code": forms.NumberInput(attrs={"class": "form-control"}),
            "employee_name": forms.TextInput(attrs={"class": "form-control"}),
            "employee_surname": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "marital_status": forms.Select(attrs={"class": "form-select"}),
            "employee_address_type": forms.Select(attrs={"class": "form-select"}),
        }

class EmployeeUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with employee data"
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run",
        help_text="Check to validate without saving to database"
    )