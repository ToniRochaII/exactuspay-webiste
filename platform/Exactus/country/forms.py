from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from Exactus.country.models import Country

# ───────────────────────────────────────────
# 1. SERVER-SIDE VALIDATOR (Python)
# ───────────────────────────────────────────
# We keep anchors (^ and $) here for strict Python validation
text_only_validator = RegexValidator(
    regex=r'^[a-zA-Z\s]+$',
    message="Invalid format: This field accepts text only (letters and spaces).",
    code='invalid_text_format'
)

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = [
            "iso2_code", "iso3_code", "name", "status", "official_language",
            "currency_name", "currency_code",
            "numbering_format", "currency_position", "date_format", "decimals", "archive",
        ]

        labels = {
            "iso2_code": "ISO 2-Letter Code",
            "iso3_code": "ISO 3-Letter Code",
            "name": "Country Name",
        }

        # ───────────────────────────────────────────
        # 2. CLIENT-SIDE WIDGETS (HTML5)
        # ───────────────────────────────────────────
        # NOTE: patterns here do NOT use ^ or $ symbols.
        widgets = {
            "iso2_code": forms.TextInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z\s]+",  # Regex for HTML (No anchors)
                "title": "Letters only (e.g. GB)",
                "placeholder": "e.g. GB"
            }),
            "iso3_code": forms.TextInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z\s]+",
                "title": "Letters only (e.g. GBR)",
                "placeholder": "e.g. GBR"
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z\s]+",
                "title": "Letters and spaces only (e.g. United Kingdom)"
            }),
            "official_language": forms.TextInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z\s]+",
                "title": "Letters only (e.g. English)"
            }),
            "currency_name": forms.TextInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z\s]+",
                "title": "Letters only (e.g. Pound Sterling)"
            }),
            "currency_code": forms.TextInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z\s]+",
                "title": "Letters only (e.g. GBP)"
            }),
            # Dropdowns
            "status": forms.Select(attrs={"class": "form-select"}),
            "numbering_format": forms.Select(attrs={"class": "form-select"}),
            "currency_position": forms.Select(attrs={"class": "form-select"}),
            "date_format": forms.Select(attrs={"class": "form-select"}),
            "decimals": forms.Select(attrs={"class": "form-select"}),
            "archive": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply the server-side validator to all text fields
        text_fields = [
            "name", 
            "iso2_code", 
            "iso3_code", 
            "official_language", 
            "currency_name", 
            "currency_code"
        ]

        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].validators.append(text_only_validator)

    def clean_iso2_code(self):
        code = self.cleaned_data["iso2_code"].upper()
        if len(code) != 2:
            raise ValidationError("ISO2 code must be exactly 2 characters.")
        return code

    def clean_iso3_code(self):
        code = self.cleaned_data["iso3_code"].upper()
        if len(code) != 3:
            raise ValidationError("ISO3 code must be exactly 3 characters.")
        return code

    def clean_currency_code(self):
        code = self.cleaned_data["currency_code"].upper()
        if len(code) != 3:
            raise ValidationError("Currency code must be exactly 3 letters.")
        return code


class CountryUploadForm(forms.Form):
    file = forms.FileField(
        label="CSV File",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"})
    )
    dry_run = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )