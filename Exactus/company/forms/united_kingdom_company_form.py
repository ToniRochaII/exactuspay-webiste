from django import forms
from Exactus.company.forms.base_company_form import BaseCompanyForm
from Exactus.company.models import Company

class UnitedKingdomCompanyForm(BaseCompanyForm):
    """
    United Kingdom Specific Company Form.
    Strictly mapped to the 'UK Company Form' visual specification and HMRC terminology.
    """

    # ──────────────────────────────────────────────────────────────
    # TAB: TAXATION 
    # ──────────────────────────────────────────────────────────────
    
    # [Row 1: Employer Settings]
    paye_ref_office_no = forms.CharField(
        label="Employer PAYE Reference Office No.", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    paye_ref_number = forms.CharField(
        label="Employer PAYE Reference Number", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # [Row 2: Accounts Office & SA UTR]
    accounts_office_ref = forms.CharField(
        label="Accounts Office Number", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    # Renamed label to SA UTR (Self Assessment) as per requirements
    sa_utr = forms.CharField(
        label="SA UTR", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # [Row 3: Company CT UTR & ECON]
    ct_utr = forms.CharField(
        label="Company CT UTR", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    # Label fixed to "ECON Reference"
    econ_reference = forms.CharField(
        label="ECON Reference", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # [Row 4: Contact & Statutory Options]
    contact_full_name = forms.CharField(
        label="Contact Full Name", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    
    # Note: 'Statutory' text field removed as per instructions.
    
    # YES/NO Dropdowns
    YES_NO_CHOICES = [("Y", "Yes"), ("N", "No")]

    small_employer_relief = forms.ChoiceField(
        label="Eligible for Small Employer Relief?", 
        choices=[("", "Select...")] + YES_NO_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "data-section": "tax"})
    )
    apprentice_levy = forms.ChoiceField(
        label="Apprentice Levy Due?", 
        choices=[("", "Select...")] + YES_NO_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "data-section": "tax"})
    )
    vat_number = forms.CharField(
        label="VAT number", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )    
    company_registration_number = forms.CharField(
        label="Company Registration Number", 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # ──────────────────────────────────────────────────────────────
    # SECTION: BANKING
    # ──────────────────────────────────────────────────────────────
    
    # [Block: Bank Account details]
    account_name = forms.CharField(
        label="Account Name", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    swift_bic = forms.CharField(
        label="Swift/BIC", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    sort_code = forms.CharField(
        label="Sort Code", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    account_number = forms.CharField(
        label="Bank Account Number", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    iban = forms.CharField(
        label="IBAN", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    
    # [Block: Bank Address]
    bank_road_1 = forms.CharField(
        label="Road Name", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    bank_town = forms.CharField(
        label="Town", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    bank_country = forms.CharField(
        label="Country", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )

    # [Block: Bacs details]
    bureau_number = forms.CharField(
        label="Bureau Number", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    bacs_user_number = forms.CharField(
        label="BACS User Number/Ref", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )
    bacs_app_number = forms.CharField(
        label="BACS Application Number", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "bank"})
    )

    class Meta(BaseCompanyForm.Meta):
        labels = {
            **BaseCompanyForm.Meta.labels,
            
            # [Tab: Company] Block: Business Details
            "company_code": "Company Code",
            "company_number": "Company Number",
            "trade_name": "Business Trade Name",
            "legal_name": "Legal Trade Name",

            # [Tab: Communication] Block: Business Details
            "contact": "Contact",
            "phone": "Telephone",
            "email": "eMail",
            "website": "website",

            # [Tab: Communication] Block: Business Address
            "building_name": "Building Name",
            "road_name_1": "Road Name",
            "road_name_2": "Road Name line 2",
            "town": "Town",
            "post_code": "Post Code",
            "county": "County",
            
            # [Block: RTI Settings]
            "rti_user_id": "User ID",
            "rti_password": "Password",

            # [Block: Account Settings]
            "account_status": "Account Status",
            "account_archive": "Account Archive",
        }

        widgets = {
            **BaseCompanyForm.Meta.widgets,
            
            # --- TAB: COMPANY ---
            "company_code": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "company_number": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),

            # --- TAB: COMMUNICATION ---
            "contact": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "data-section": "communication"}),
            "website": forms.URLInput(attrs={"class": "form-control", "data-section": "communication"}),
            
            # MOVED ADDRESS TO COMMUNICATION TAB
            "building_name": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "road_name_1": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "road_name_2": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "town": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "post_code": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "county": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            
            # --- TAB: TAXATION / RTI ---
            "rti_user_id": forms.TextInput(attrs={"class": "form-control", "data-section": "tax"}),
            "rti_password": forms.PasswordInput(
                attrs={"class": "form-control", "data-section": "tax", "autocomplete": "new-password"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate custom fields from DB when editing
        if self.instance and self.instance.pk:
            # === Map Tax IDs (Matches Truth Table) ===
            self.fields["paye_ref_office_no"].initial = self.instance.tax_id_01 or ""
            self.fields["paye_ref_number"].initial = self.instance.tax_id_02 or ""
            self.fields["accounts_office_ref"].initial = self.instance.tax_id_03 or ""
            self.fields["sa_utr"].initial = self.instance.tax_id_04 or "" # Mapped to 04
            self.fields["ct_utr"].initial = self.instance.tax_id_05 or ""
            self.fields["econ_reference"].initial = self.instance.tax_id_06 or ""
            self.fields["contact_full_name"].initial = self.instance.tax_id_07 or ""
            
            # tax_id_08 was Statutory - Skipped/Deleted
            
            self.fields["small_employer_relief"].initial = self.instance.tax_id_08 or ""
            self.fields["apprentice_levy"].initial = self.instance.tax_id_09 or ""
            self.fields["vat_number"].initial = self.instance.tax_id_10 or ""
            self.fields["company_registration_number"].initial = self.instance.tax_id_11 or ""

            # === Map Bank Fields ===
            self.fields["account_name"].initial = self.instance.bank_01 or ""
            self.fields["swift_bic"].initial = self.instance.bank_02 or ""
            self.fields["sort_code"].initial = self.instance.bank_03 or ""
            self.fields["account_number"].initial = self.instance.bank_04 or ""
            self.fields["iban"].initial = self.instance.bank_05 or ""
            self.fields["bank_road_1"].initial = self.instance.bank_06 or ""
            self.fields["bank_town"].initial = self.instance.bank_07 or ""
            self.fields["bank_country"].initial = self.instance.bank_08 or ""
            self.fields["bureau_number"].initial = self.instance.bank_09 or ""
            self.fields["bacs_user_number"].initial = self.instance.bank_10 or ""
            self.fields["bacs_app_number"].initial = self.instance.bank_11 or ""

        # Hide generic slots to avoid duplicates in UI
        for name, field in self.fields.items():
            if name.startswith(("tax_id_", "bank_")) and name not in [
                "tax_id_01", "tax_id_02", "tax_id_03", "tax_id_04", "tax_id_05",
                "tax_id_06", "tax_id_07", "tax_id_08", "tax_id_09", "tax_id_10", "tax_id_11",
                "bank_01", "bank_02", "bank_03", "bank_04", "bank_05",
                "bank_06", "bank_07", "bank_08", "bank_09", "bank_10", "bank_11"
            ]:
                field.widget = forms.HiddenInput()

    def save(self, commit=True):
        company = super().save(commit=False)
        
        # Save Tax Data
        company.tax_id_01 = self.cleaned_data.get("paye_ref_office_no", "")
        company.tax_id_02 = self.cleaned_data.get("paye_ref_number", "")
        company.tax_id_03 = self.cleaned_data.get("accounts_office_ref", "")
        company.tax_id_04 = self.cleaned_data.get("sa_utr", "")
        company.tax_id_05 = self.cleaned_data.get("ct_utr", "")
        company.tax_id_06 = self.cleaned_data.get("econ_reference", "")
        company.tax_id_07 = self.cleaned_data.get("contact_full_name", "")
        
        # tax_id_08 is unused (was Statutory)
        company.tax_id_08 = self.cleaned_data.get("small_employer_relief", "")
        
        company.tax_id_09 = self.cleaned_data.get("apprentice_levy", "")
        company.tax_id_10 = self.cleaned_data.get("vat_number", "")
        company.tax_id_11 = self.cleaned_data.get("company_registration_number", "")

        # Save Bank Data
        company.bank_01 = self.cleaned_data.get("account_name", "")
        company.bank_02 = self.cleaned_data.get("swift_bic", "")
        company.bank_03 = self.cleaned_data.get("sort_code", "")
        company.bank_04 = self.cleaned_data.get("account_number", "")
        company.bank_05 = self.cleaned_data.get("iban", "")
        company.bank_06 = self.cleaned_data.get("bank_road_1", "")
        company.bank_07 = self.cleaned_data.get("bank_town", "")
        company.bank_08 = self.cleaned_data.get("bank_country", "")
        company.bank_09 = self.cleaned_data.get("bureau_number", "")
        company.bank_10 = self.cleaned_data.get("bacs_user_number", "")
        company.bank_11 = self.cleaned_data.get("bacs_app_number", "")

        if commit:
            company.save()
        return company