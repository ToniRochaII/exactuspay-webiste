from django import forms
from .models import (
    Employee,
)


# ───────────────────────────────
# 👥 Employee Form
# ───────────────────────────────
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
        }