# Exactus/company/forms/uk_company_form.py

from django import forms
from django.core.exceptions import ValidationError
import re
from .base_company_form import BaseCompanyForm

class UnitedKingdomCompanyForm(BaseCompanyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Labels
        self.fields['company_number'].label = "Company Registration Number"
        self.fields['tax_id_01'].label = "PAYE Reference"
        self.fields['tax_id_02'].label = "Accounts Office Reference"
        self.fields['tax_id_03'].label = "VAT Registration Number"
        self.fields['bank_03'].label = "Sort Code"
        self.fields['bank_05'].label = "IBAN"

        # 2. Helpers
        self.fields['tax_id_01'].help_text = "Format: 123/X12345"
        self.fields['bank_03'].widget.attrs['placeholder'] = "00-00-00"

        # 3. Required
        self.fields['tax_id_01'].required = True
        self.fields['post_code'].required = True

    def clean_bank_03(self):
        """Validate Sort Code"""
        sort_code = self.cleaned_data.get("bank_03")
        if sort_code:
            digits = "".join(d for d in sort_code if d.isdigit())
            if len(digits) != 6:
                raise ValidationError("Sort Code must contain 6 digits.")
        return sort_code

    def clean_tax_id_03(self):
        """Validate VAT"""
        vat = self.cleaned_data.get("tax_id_03")
        if vat and vat.upper().startswith("GB"):
            if len(vat) < 5: 
                raise ValidationError("Invalid VAT format.")
        return vat