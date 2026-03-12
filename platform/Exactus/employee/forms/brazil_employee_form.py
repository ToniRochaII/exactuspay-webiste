from django import forms
from django.core.exceptions import ValidationError
import re

from Exactus.employee.forms.base_employee_form import BaseEmployeeForm
from Exactus.employee.models import Employee

class BrazilEmployeeForm(BaseEmployeeForm):
    """
    Brazil-specific Employee Form.
    - Labels mapped to British English.
    - Corrected Address Structure (Street, Number, District, etc.).
    - Corrected Banking Structure (Bank, Branch, Account).
    - BACS Removed.
    """

    # ==========================
    # TAXATION FIELDS (Virtual Fields)
    # ==========================
    
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
        help_text="Individual Taxpayer Registry",
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
        help_text="Social Integration Program Number",
    )

    rg_number = forms.CharField(
        max_length=20,
        required=False,
        label="Identity Card (RG)",
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "data-section": "tax",
            "placeholder": "00.000.000-0"
        }),
    )

    ctps_number = forms.CharField(
        max_length=20,
        required=True,
        label="Work Permit Number (CTPS)",
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "data-section": "tax",
            "placeholder": "1234567"
        }),
    )

    ctps_series = forms.CharField(
        max_length=10,
        required=True,
        label="Work Permit Series",
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "data-section": "tax",
            "placeholder": "0000"
        }),
    )

    ctps_uf = forms.CharField(
        max_length=2,
        required=True,
        label="Work Permit State",
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "data-section": "tax",
            "placeholder": "SP"
        }),
    )

    # ==========================
    # Meta configuration
    # ==========================

    class Meta(BaseEmployeeForm.Meta):
        model = Employee
        
        # 1. Override Labels to British English descriptions
        labels = {
            **BaseEmployeeForm.Meta.labels,
            
            # Communication - Address
            "employee_address_01": "Street Address",
            "employee_address_02": "Number",
            "employee_address_03": "Complement",
            "employee_address_04": "District",
            "employee_address_05": "City",
            "employee_address_06": "Post Code",
            "employee_address_07": "State",

            # Banking - Account Details
            "bank_01": "Bank Name",
            "bank_02": "Account Holder Name",
            "bank_03": "Branch Code",
            "bank_04": "Account Number",
            "bank_05": "Account Type",
            "bank_07": "PIX Key (Optional)", 
            "bank_08": "SWIFT/BIC",
            
            # Banking - Address
            "bank_11": "Bank Address (Street)",
            "bank_12": "Number",
            "bank_13": "District",
            "bank_14": "City",
            "bank_15": "State",
            "bank_16": "Post Code",
        }

        # 2. Field Order
        fields = [
            # Standard Fields
            "employee_id", "employee_number", "employee_code", 
            "employee_name", "employee_surname", "gender", "date_of_birth", 
            "marital_status", 
            
            # Communication & Address
            "email", "telephone",
            "employee_address_type", "employee_address_01", "employee_address_02",
            "employee_address_03", "employee_address_04", "employee_address_05",
            "employee_address_06", "employee_address_07",
            
            # Job / Payroll
            "employment_start_date", "employment_end_date",
            "department", "cost_centre", "job_title", "position_number", "fte",
            
            # Banking - Explicitly listing 01-16 (NO BACS)
            "bank_01", "bank_02", "bank_03", "bank_04", "bank_05", 
            "bank_06", "bank_07", "bank_08", "bank_09", "bank_10",
            "bank_11", "bank_12", "bank_13", "bank_14", "bank_15", "bank_16",
            
            # Virtual Tax Fields
            "cpf", "pis", "rg_number", "ctps_number", "ctps_series", "ctps_uf",
            
            # Hidden Generic Storage Fields
            *[f"tax_info_{i:02d}" for i in range(1, 21)]
        ]

    # ==========================
    # Initialisation
    # ==========================

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. REMOVE BACS Fields
        bacs_fields = ["bank_17", "bank_18", "bank_19", "bank_20"]
        for f in bacs_fields:
            if f in self.fields:
                del self.fields[f]

        # 2. FORCE Banking & Address Labels (British English)
        field_overrides = {
            # Address
            "employee_address_01": "Street Address",
            "employee_address_02": "Number",
            "employee_address_03": "Complement",
            "employee_address_04": "District",
            "employee_address_05": "City",
            "employee_address_06": "Post Code",
            "employee_address_07": "State",
            
            # Banking
            "bank_01": "Bank Name",
            "bank_02": "Account Holder Name",
            "bank_03": "Branch Code",
            "bank_04": "Account Number",
            "bank_05": "Account Type",
            "bank_11": "Bank Address (Street)",
            "bank_12": "Number",
            "bank_13": "District",
            "bank_14": "City",
            "bank_15": "State",
            "bank_16": "Post Code",
        }

        for field_name, label in field_overrides.items():
            if field_name in self.fields:
                self.fields[field_name].label = label
                # Ensure correct section mapping
                if "employee_address" in field_name:
                    self.fields[field_name].widget.attrs["data-section"] = "communication"
                elif "bank" in field_name:
                    self.fields[field_name].widget.attrs["data-section"] = "bank"
                
                self.fields[field_name].widget.attrs["placeholder"] = " "

        # 3. SETUP Taxation Fields
        if self.instance and self.instance.pk:
            self.fields["cpf"].initial = self.instance.tax_info_01
            self.fields["pis"].initial = self.instance.tax_info_02
            self.fields["rg_number"].initial = self.instance.tax_info_03
            self.fields["ctps_number"].initial = self.instance.tax_info_04
            self.fields["ctps_series"].initial = self.instance.tax_info_05
            self.fields["ctps_uf"].initial = self.instance.tax_info_06

        # Hide generic storage fields
        for i in range(1, 21):
            field_name = f"tax_info_{i:02d}"
            if field_name in self.fields:
                self.fields[field_name].widget = forms.HiddenInput()
                self.fields[field_name].label = ""

        # Ensure Virtual Fields have 'tax' section
        virtual_tax_fields = ["cpf", "pis", "rg_number", "ctps_number", "ctps_series", "ctps_uf"]
        for f in virtual_tax_fields:
            if f in self.fields:
                self.fields[f].widget.attrs["data-section"] = "tax"
                self.fields[f].widget.attrs["class"] = "form-control"

    # ==========================
    # Validation
    # ==========================
    def clean_cpf(self):
        raw_cpf = self.cleaned_data.get("cpf", "")
        cpf = re.sub(r"\D", "", raw_cpf)
        if len(cpf) != 11:
            raise ValidationError("CPF must contain exactly 11 digits.")
        return cpf

    def clean_pis(self):
        raw_pis = self.cleaned_data.get("pis", "")
        pis = re.sub(r"\D", "", raw_pis)
        if len(pis) != 11:
            raise ValidationError("PIS/PASEP must contain exactly 11 digits.")
        return pis
    
    # ==========================
    # Persistence
    # ==========================
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        employee.tax_info_01 = self.cleaned_data.get("cpf", "")
        employee.tax_info_02 = self.cleaned_data.get("pis", "")
        employee.tax_info_03 = self.cleaned_data.get("rg_number", "")
        employee.tax_info_04 = self.cleaned_data.get("ctps_number", "")
        employee.tax_info_05 = self.cleaned_data.get("ctps_series", "")
        employee.tax_info_06 = self.cleaned_data.get("ctps_uf", "")

        if commit:
            employee.save()
        return employee