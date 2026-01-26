import re
from django import forms
from django.core.exceptions import ValidationError
from Exactus.employee.models import Employee
from .base_employee_form import BaseEmployeeForm

class UnitedKingdomEmployeeForm(BaseEmployeeForm):
    """
    United Kingdom-specific Employee Form.
    - Customizes Banking Labels (Sort Code format 00-00-00).
    - Implements specific Taxation Blocks.
    """

    # ==========================================================================
    # TAXATION FIELDS (Virtual fields mapped to generic DB columns)
    # ==========================================================================
    
    # --- Block 1: Documentation ---
    ni_number = forms.CharField(
        label="National Insurance Number",
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "AB123456C", "data-section": "tax"})
    )
    passport_number = forms.CharField(
        label="Passport Number",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # --- Block 2: Taxation ---
    tax_code = forms.CharField(
        label="Tax Code",
        help_text="Numbers required. Letters optional (e.g., 1257L).",
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "1257L", "data-section": "tax"})
    )
    tax_basis = forms.ChoiceField(
        label="Tax Basis",
        choices=[("CUMULATIVE", "Cumulative"), ("NON_CUMULATIVE", "Week 1 / Month 1")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-section": "tax"})
    )
    ni_category = forms.CharField(
        label="NI Category",
        max_length=1,
        help_text="e.g., A, M, H, etc.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "A", "data-section": "tax"})
    )

    # --- Block 3: P45 Details ---
    p45_tax_code = forms.CharField(
        label="P45 Tax Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    p45_tax_basis = forms.ChoiceField(
        label="P45 Tax Basis",
        choices=[("", "Select..."), ("CUMULATIVE", "Cumulative"), ("NON_CUMULATIVE", "Week 1 / Month 1")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-section": "tax"})
    )
    p45_gross_earnings = forms.DecimalField(
        label="P45 Gross Earnings to Date",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "data-section": "tax"})
    )
    p45_tax_paid = forms.DecimalField(
        label="P45 Tax to Date",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "data-section": "tax"})
    )

    # --- Block 4: Starter Declaration ---
    starter_declaration = forms.ChoiceField(
        label="Starter Declaration",
        choices=[
            ("", "Select Statement..."),
            ("A", "A: First job since 6 April"),
            ("B", "B: Only job now"),
            ("C", "C: Have another job/pension"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-section": "tax"})
    )
    starter_student_loan = forms.ChoiceField(
        label="Starter Student Loan",
        choices=[("", "None"), ("PLAN1", "Plan 1"), ("PLAN2", "Plan 2"), ("PLAN4", "Plan 4")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-section": "tax"})
    )

    # --- Block 5: Student Loans ---
    has_student_loan = forms.BooleanField(
        label="Has Student Loan?",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "data-section": "tax"})
    )
    student_loan_plan = forms.ChoiceField(
        label="Student Loan Plan Type",
        choices=[("", "Select..."), ("PLAN1", "Plan 1"), ("PLAN2", "Plan 2"), ("PLAN4", "Plan 4")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-section": "tax"})
    )
    has_pg_loan = forms.BooleanField(
        label="PG Student Loan?",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "data-section": "tax"})
    )
    loan_start_date = forms.DateField(
        label="Loan Start Date",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date", "data-section": "tax"})
    )
    loan_end_date = forms.DateField(
        label="Loan End Date",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date", "data-section": "tax"})
    )

    # --- Block 6: Director Details ---
    is_director = forms.BooleanField(
        label="Is Director?",
        required=False,
        help_text="Check if the employee is a company director.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "data-section": "tax"})
    )
    director_appointment_date = forms.DateField(
        label="Director Appointment Date",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date", "data-section": "tax"})
    )
    director_nic_method = forms.ChoiceField(
        label="Director NIC Method",
        choices=[
            ("STANDARD", "Standard (Annual/Cumulative)"),
            ("ALTERNATIVE", "Alternative (Table Method)")
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "data-section": "tax"})
    )

    # --- Block 7: Other ---
    irregular_employment = forms.BooleanField(
        label="Irregular Payment Pattern?",
        required=False,
        help_text="Check for casual or seasonal workers.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "data-section": "tax"})
    )

    class Meta(BaseEmployeeForm.Meta):
        model = Employee
        
        # 1. Override Labels to match UK terminology
        labels = {
            **BaseEmployeeForm.Meta.labels,
            # Address
            "employee_address_01": "Building and Street",
            "employee_address_03": "Town or City",
            "employee_address_04": "County",
            "employee_address_06": "Postcode",

            # Banking - Account Details
            "bank_01": "Bank Name",
            "bank_02": "Account Name",
            "bank_03": "Sort Code",          # CHANGED from Branch Code
            "bank_04": "Account Number",
            "bank_07": "IBAN",
            "bank_08": "Swift/BIC",
            
            # Banking - Address
            "bank_11": "Road Name",
            "bank_12": "Road Name line 2",
            "bank_13": "Town",
            "bank_14": "Post Code",
            "bank_16": "Country",

            # Banking - BACS
            "bank_17": "Bureau Number",
            "bank_18": "BACS User Number/Ref",
            "bank_19": "BACS Application Number",
        }

        # 2. Define Field Order
        fields = [
            # Standard
            "employee_id", "employee_number", "employee_code", 
            "employee_name", "employee_surname", "gender", "date_of_birth", 
            "marital_status", 
            
            # Communication & Address
            "email", "telephone",
            "employee_address_type", "employee_address_01", "employee_address_02",
            "employee_address_03", "employee_address_04", "employee_address_05",
            "employee_address_06", "employee_address_07",
            
            # Job
            "employment_start_date", "employment_end_date",
            "department", "cost_centre", "job_title", "position_number", "fte",
            
            # Banking
            *[f"bank_{i:02d}" for i in range(1, 21)],

            # Virtual Tax Fields
            "ni_number", "passport_number",              
            "tax_code", "tax_basis", "ni_category",      
            "p45_tax_code", "p45_tax_basis", "p45_gross_earnings", "p45_tax_paid", 
            "starter_declaration", "starter_student_loan", 
            "has_student_loan", "student_loan_plan", "has_pg_loan", "loan_start_date", "loan_end_date", 
            
            # New Director & Irregular fields
            "is_director", "director_appointment_date", "director_nic_method", "irregular_employment",

            # Generic Storage Fields (Will be hidden)
            *[f"tax_info_{i:02d}" for i in range(1, 21)]
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. LOAD DATA: Map Generic DB columns -> Specific Form Fields
        if self.instance and self.instance.pk:
            self.fields["ni_number"].initial = self.instance.tax_info_01
            self.fields["passport_number"].initial = self.instance.tax_info_02
            self.fields["tax_code"].initial = self.instance.tax_info_03
            self.fields["tax_basis"].initial = self.instance.tax_info_04
            self.fields["ni_category"].initial = self.instance.tax_info_05
            self.fields["p45_tax_code"].initial = self.instance.tax_info_06
            self.fields["p45_tax_basis"].initial = self.instance.tax_info_07
            self.fields["p45_gross_earnings"].initial = self.instance.tax_info_08
            self.fields["p45_tax_paid"].initial = self.instance.tax_info_09
            self.fields["starter_declaration"].initial = self.instance.tax_info_10
            self.fields["starter_student_loan"].initial = self.instance.tax_info_11
            
            # Boolean conversions
            self.fields["has_student_loan"].initial = str(self.instance.tax_info_12).lower() == 'true'
            self.fields["student_loan_plan"].initial = self.instance.tax_info_13
            self.fields["has_pg_loan"].initial = str(self.instance.tax_info_14).lower() == 'true'
            
            # Dates (loaded as strings, which DateInput handles fine)
            self.fields["loan_start_date"].initial = self.instance.tax_info_15
            self.fields["loan_end_date"].initial = self.instance.tax_info_16
            
            self.fields["is_director"].initial = str(self.instance.tax_info_17).lower() == 'true'
            self.fields["director_appointment_date"].initial = self.instance.tax_info_18
            self.fields["director_nic_method"].initial = self.instance.tax_info_19
            self.fields["irregular_employment"].initial = str(self.instance.tax_info_20).lower() == 'true'

        # 2. HIDE STORAGE FIELDS
        for i in range(1, 21):
            field_name = f"tax_info_{i:02d}"
            if field_name in self.fields:
                self.fields[field_name].widget = forms.HiddenInput()

        # 3. SET SECTIONS
        custom_tax_fields = [
            "ni_number", "passport_number",
            "tax_code", "tax_basis", "ni_category",
            "p45_tax_code", "p45_tax_basis", "p45_gross_earnings", "p45_tax_paid",
            "starter_declaration", "starter_student_loan",
            "has_student_loan", "student_loan_plan", "has_pg_loan", "loan_start_date", "loan_end_date",
            "is_director", "director_appointment_date", "director_nic_method", "irregular_employment"
        ]
        
        for field in custom_tax_fields:
            if field in self.fields:
                self.fields[field].widget.attrs["data-section"] = "tax"
                if isinstance(self.fields[field].widget, forms.CheckboxInput):
                    self.fields[field].widget.attrs["class"] = "form-check-input"
                else:
                    self.fields[field].widget.attrs["class"] = "form-control"

        # 4. SET BANKING SECTIONS & SPECIFIC FORMATS
        for i in range(1, 21):
            bank_field = f"bank_{i:02d}"
            if bank_field in self.fields:
                self.fields[bank_field].widget.attrs["data-section"] = "bank"
                self.fields[bank_field].widget.attrs["class"] = "form-control"
                
                # Apply specific placeholder for Sort Code (bank_03)
                if bank_field == "bank_03":
                    self.fields[bank_field].widget.attrs["placeholder"] = "00-00-00"
                    self.fields[bank_field].help_text = "Format: 00-00-00"

    def clean_ni_number(self):
        ni = self.cleaned_data.get("ni_number", "").upper().replace(" ", "")
        pattern = r'^(?!BG|GB|KN|NK|NT|TN|ZZ)[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$'
        if not re.match(pattern, ni):
            raise ValidationError("Invalid National Insurance Number")
        return ni

    def clean_bank_03(self):
        # Sort Code Validation
        sort_code = self.cleaned_data.get("bank_03", "")
        if sort_code:
            # Allow 00-00-00 or 000000
            digits = re.sub(r"\D", "", sort_code)
            if len(digits) != 6:
                raise ValidationError("Sort code must contain exactly 6 digits.")
            # Auto-format
            return f"{digits[:2]}-{digits[2:4]}-{digits[4:]}"
        return sort_code

    def save(self, commit=True):
        employee = super().save(commit=False)

        # 5. SAVE DATA: Map Virtual Form Fields -> Generic DB Columns
        employee.tax_info_01 = self.cleaned_data.get("ni_number")
        employee.tax_info_02 = self.cleaned_data.get("passport_number")
        employee.tax_info_03 = self.cleaned_data.get("tax_code")
        employee.tax_info_04 = self.cleaned_data.get("tax_basis")
        employee.tax_info_05 = self.cleaned_data.get("ni_category")
        employee.tax_info_06 = self.cleaned_data.get("p45_tax_code")
        employee.tax_info_07 = self.cleaned_data.get("p45_tax_basis")
        employee.tax_info_08 = self.cleaned_data.get("p45_gross_earnings")
        employee.tax_info_09 = self.cleaned_data.get("p45_tax_paid")
        employee.tax_info_10 = self.cleaned_data.get("starter_declaration")
        employee.tax_info_11 = self.cleaned_data.get("starter_student_loan")
        
        employee.tax_info_12 = str(self.cleaned_data.get("has_student_loan", False))
        employee.tax_info_13 = self.cleaned_data.get("student_loan_plan")
        employee.tax_info_14 = str(self.cleaned_data.get("has_pg_loan", False))
        
        # FIX: Convert Date objects to Strings for storage in CharFields
        loan_start = self.cleaned_data.get("loan_start_date")
        employee.tax_info_15 = str(loan_start) if loan_start else None

        loan_end = self.cleaned_data.get("loan_end_date")
        employee.tax_info_16 = str(loan_end) if loan_end else None
        
        employee.tax_info_17 = str(self.cleaned_data.get("is_director", False))
        
        # FIX: Convert Date object to String
        appt_date = self.cleaned_data.get("director_appointment_date")
        employee.tax_info_18 = str(appt_date) if appt_date else None
        
        employee.tax_info_19 = self.cleaned_data.get("director_nic_method")
        employee.tax_info_20 = str(self.cleaned_data.get("irregular_employment", False))

        if commit:
            employee.save()
        return employee