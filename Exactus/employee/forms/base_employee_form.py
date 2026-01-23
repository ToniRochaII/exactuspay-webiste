from django import forms
from django.core.exceptions import ValidationError
from Exactus.employee.models import Employee

class BaseEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ["company"]

        # Define labels for clarity (generic defaults)
        labels = {
            "employee_id": "Employee ID",
            "employee_number": "Employee Number",
            "employee_code": "Employee Code",
            "employee_name": "First Name",
            "employee_surname": "Last Name",
            "gender": "Gender",
            "date_of_birth": "Date of Birth",
            "marital_status": "Marital Status",
            
            # Communications
            "email": "Email Address",
            "telephone": "Telephone Number",
            
            # Address 01-07 mapped in widgets
            "employee_address_type": "Address Type",
            
            # Job
            "employment_start_date": "Start Date",
            "employment_end_date": "Termination Date",
            "department": "Department",
            "cost_centre": "Cost Centre",
            "job_title": "Job Title",
            "position_number": "Position Number",
            "fte": "Full-Time Equivalent",
        }

        widgets = {
            # --- Personal Information ---
            "employee_id": forms.TextInput(attrs={"class": "form-control", "data-section": "personal"}),
            "employee_number": forms.NumberInput(attrs={"class": "form-control", "data-section": "personal"}),
            "employee_code": forms.NumberInput(attrs={"class": "form-control", "data-section": "personal"}),
            "employee_name": forms.TextInput(attrs={"class": "form-control", "data-section": "personal"}),
            "employee_surname": forms.TextInput(attrs={"class": "form-control", "data-section": "personal"}),
            "gender": forms.Select(attrs={"class": "form-control", "data-section": "personal"}),
            "marital_status": forms.Select(attrs={"class": "form-control", "data-section": "personal"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date", "data-section": "personal"}),

            # --- Communication & Address Information (Renamed Section) ---
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "name@example.com", "data-section": "communication"}),
            "telephone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 234 567 890", "data-section": "communication"}),
            
            "employee_address_type": forms.Select(attrs={"class": "form-control", "data-section": "communication"}),
            "employee_address_01": forms.TextInput(attrs={"class": "form-control", "placeholder": "Address Line 1", "data-section": "communication"}),
            "employee_address_02": forms.TextInput(attrs={"class": "form-control", "placeholder": "Address Line 2", "data-section": "communication"}),
            "employee_address_03": forms.TextInput(attrs={"class": "form-control", "placeholder": "Address Line 3", "data-section": "communication"}),
            "employee_address_04": forms.TextInput(attrs={"class": "form-control", "placeholder": "City", "data-section": "communication"}),
            "employee_address_05": forms.TextInput(attrs={"class": "form-control", "placeholder": "State/Province", "data-section": "communication"}),
            "employee_address_06": forms.TextInput(attrs={"class": "form-control", "placeholder": "Postal Code", "data-section": "communication"}),
            "employee_address_07": forms.TextInput(attrs={"class": "form-control", "placeholder": "Country", "data-section": "communication"}),

            # --- Job Information ---
            "department": forms.TextInput(attrs={"class": "form-control", "data-section": "job"}),
            "cost_centre": forms.TextInput(attrs={"class": "form-control", "data-section": "job"}),
            "job_title": forms.TextInput(attrs={"class": "form-control", "data-section": "job"}),
            "position_number": forms.TextInput(attrs={"class": "form-control", "data-section": "job"}),
            "fte": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "data-section": "job"}),
            "employment_start_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "data-section": "job"}),
            "employment_end_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "data-section": "job"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ─────────────────────────────────────────────────────────────────
        # AUTOMATICALLY GENERATE WIDGETS FOR BANK_01...20 AND TAX_01...20
        # ─────────────────────────────────────────────────────────────────
        
        # 1. Bank Fields (bank_01 to bank_20)
        for i in range(1, 21):
            field_name = f"bank_{i:02d}"
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    "class": "form-control",
                    "placeholder": " ",
                    "data-section": "bank"
                })
                # Set a generic label if none exists
                if not self.fields[field_name].label:
                    self.fields[field_name].label = f"Bank Field {i}"

        # 2. Tax Fields (tax_info_01 to tax_info_20)
        for i in range(1, 21):
            field_name = f"tax_info_{i:02d}"
            if field_name in self.fields:
                # Default widget attributes
                attrs = {
                    "class": "form-control",
                    "placeholder": " ",
                    "data-section": "tax"
                }
                
                # Special handling for known date fields
                if i in [5, 6, 16, 17]:
                    self.fields[field_name].widget = forms.DateInput(attrs={**attrs, "type": "date"})
                else:
                    self.fields[field_name].widget = forms.TextInput(attrs=attrs)
                
                if not self.fields[field_name].label:
                     self.fields[field_name].label = f"Tax Field {i}"

    # Cleaning methods
    def clean_employee_id(self):
        eid = (self.cleaned_data.get("employee_id") or "").strip()
        return eid or None

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

class EmployeeUploadForm(forms.Form):
    file = forms.FileField()
    dry_run = forms.BooleanField(required=False)