# Exactus/company/forms/brazil_company_form.py

from django import forms
from django.core.exceptions import ValidationError
import re
from .base_company_form import BaseCompanyForm

class BrazilCompanyForm(BaseCompanyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Label Overrides
        labels = {
            "company_number": "Número da Empresa",
            "trade_name": "Nome Fantasia",
            "legal_name": "Razão Social",
            "tax_id_01": "CNPJ",
            "tax_id_02": "Inscrição Estadual (IE)",
            "tax_id_03": "Inscrição Municipal (IM)",
            "post_code": "CEP",
            "town": "Cidade",
            "county": "Estado",
            "bank_03": "Número da Agência",
            "bank_05": "Número da Conta",
        }
        for field, label in labels.items():
            if field in self.fields:
                self.fields[field].label = label

        # 2. Placeholders
        self.fields["tax_id_01"].widget.attrs["placeholder"] = "00.000.000/0000-00"
        self.fields["post_code"].widget.attrs["placeholder"] = "00000-000"

        # 3. Required Fields
        required_fields = ["trade_name", "legal_name", "tax_id_01", "post_code", "town"]
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True

        # 4. Hide Unused Fields
        hidden_fields = ["rti_user_id", "rti_password", "tax_id_10", "tax_id_11"]
        for field in hidden_fields:
            if field in self.fields:
                self.fields[field].widget = forms.HiddenInput()

    def clean_tax_id_01(self):
        """Validate CNPJ"""
        cnpj = self.cleaned_data.get("tax_id_01")
        if not cnpj:
            return cnpj
        
        # Strip non-digits
        cnpj = re.sub(r'\D', '', cnpj)
        
        if len(cnpj) != 14:
            raise ValidationError("O CNPJ deve conter 14 dígitos.")
        
        # (Insert your CNPJ specific validation logic here...)
        return cnpj

    def clean_post_code(self):
        """Validate CEP"""
        cep = self.cleaned_data.get("post_code", "")
        if cep:
            cep = re.sub(r'\D', '', cep)
            if len(cep) != 8:
                raise ValidationError("CEP deve conter 8 dígitos.")
        return cep