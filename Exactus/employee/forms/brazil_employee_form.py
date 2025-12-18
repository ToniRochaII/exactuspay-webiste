from django import forms
from django.core.exceptions import ValidationError
import re

from Exactus.employee.forms.base_employee_form import BaseEmployeeForm


class BrazilEmployeeForm(BaseEmployeeForm):
    """
    Brazil-specific Employee Form

    This form:
    - Exposes CPF and PIS as first-class fields
    - Maps them internally to tax_info_01 and tax_info_02
    - Hides the generic tax_info fields
    - Ensures consistent edit + save behaviour
    """

    # ==========================
    # Brazil-specific fields
    # ==========================

    cpf = forms.CharField(
        max_length=14,
        required=True,
        label="CPF",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.000.000-00",
            "data-mask": "000.000.000-00",
            "data-section": "personal",
        }),
        help_text="Brazilian individual taxpayer registry (CPF)",
    )

    pis = forms.CharField(
        max_length=14,
        required=True,
        label="PIS / PASEP",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "000.00000.00-0",
            "data-mask": "000.00000.00-0",
            "data-section": "personal",
        }),
        help_text="Brazilian social integration program number",
    )

    ctps_number = forms.CharField(
        max_length=20,
        required=False,
        label="CTPS Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": " ",
            "data-section": "personal",
        }),
        help_text="Brazilian work permit number (CTPS)",
    )

    # ==========================
    # Meta configuration
    # ==========================

    class Meta(BaseEmployeeForm.Meta):
        """
        We inherit everything from BaseEmployeeForm and:
        - Keep tax_info fields included (so they can be saved)
        - Override labels for Brazil-specific meaning
        """
        labels = {
            **BaseEmployeeForm.Meta.labels,
            "tax_info_01": "CPF",
            "tax_info_02": "PIS / PASEP",
            "tax_info_03": "CTPS",
        }

        exclude = BaseEmployeeForm.Meta.exclude

    # ==========================
    # Initialisation
    # ==========================

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate Brazil-specific fields when editing
        if self.instance and self.instance.pk:
            self.fields["cpf"].initial = self.instance.tax_info_01 or ""
            self.fields["pis"].initial = self.instance.tax_info_02 or ""

        # Hide the generic tax_info fields from the UI
        for field_name in ("tax_info_01", "tax_info_02", "tax_info_03"):
            if field_name in self.fields:
                self.fields[field_name].widget = forms.HiddenInput()

        # Ensure Bootstrap floating labels work
        for field in self.fields.values():
            field.widget.attrs.setdefault("placeholder", " ")

    # ==========================
    # Validation
    # ==========================

    def clean_cpf(self):
        """
        Validate and normalize CPF (store digits only).
        """
        raw_cpf = self.cleaned_data.get("cpf", "")
        cpf = re.sub(r"\D", "", raw_cpf)

        if len(cpf) != 11:
            raise ValidationError(
                "CPF must contain exactly 11 digits (e.g. 123.456.789-09)"
            )

        return cpf

    def clean_pis(self):
        """
        Validate and normalize PIS/PASEP (store digits only).
        """
        raw_pis = self.cleaned_data.get("pis", "")
        pis = re.sub(r"\D", "", raw_pis)

        if len(pis) != 11:
            raise ValidationError(
                "PIS/PASEP must contain exactly 11 digits (e.g. 123.45678.90-1)"
            )

        return pis

    # ==========================
    # Persistence
    # ==========================

    def save(self, commit=True):
        """
        Save employee and map Brazil-specific fields to tax_info fields.
        """
        employee = super().save(commit=False)

        # Map Brazil fields → generic tax fields
        employee.tax_info_01 = self.cleaned_data.get("cpf", "")
        employee.tax_info_02 = self.cleaned_data.get("pis", "")

        if commit:
            employee.save()

        return employee
