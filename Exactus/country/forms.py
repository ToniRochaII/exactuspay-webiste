from django import forms
from django.core.exceptions import ValidationError
from Exactus.country.models import Country


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = [
            "iso2_code", "iso3_code", "name", "status", "official_language",
            "currency_name", "currency_code", "fiscal_year_start", "fiscal_year_end",
            "numbering_format", "currency_position", "date_format", "decimals", "archive",
        ]

        labels = {
            "iso2_code": "ISO 2-Letter Code",
            "iso3_code": "ISO 3-Letter Code",
            "name": "Country Name",
        }

        widgets = {
            # Text fields
            "iso2_code": forms.TextInput(attrs={"class": "form-control"}),
            "iso3_code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "official_language": forms.TextInput(attrs={"class": "form-control"}),
            "currency_name": forms.TextInput(attrs={"class": "form-control"}),
            "currency_code": forms.TextInput(attrs={"class": "form-control"}),
            "fiscal_year_start": forms.TextInput(attrs={"class": "form-control"}),
            "fiscal_year_end": forms.TextInput(attrs={"class": "form-control"}),

            # Dropdowns
            "status": forms.Select(attrs={"class": "form-control"}),
            "numbering_format": forms.Select(attrs={"class": "form-control"}),
            "currency_position": forms.Select(attrs={"class": "form-control"}),
            "date_format": forms.Select(attrs={"class": "form-control"}),
            "decimals": forms.Select(attrs={"class": "form-control"}),
            "archive": forms.Select(attrs={"class": "form-control"}),
        }

    # ───────────────────────────────────────────
    # CLEANING METHODS
    # ───────────────────────────────────────────

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
            raise ValidationError("Currency code must be exactly 3 letters (e.g. EUR, USD).")
        return code

    def clean(self):
        cleaned = super().clean()

        fy_start = cleaned.get("fiscal_year_start")
        fy_end = cleaned.get("fiscal_year_end")

        # Basic fiscal year sanity check
        if fy_start and fy_end and fy_start == fy_end:
            raise ValidationError("Fiscal year start and end cannot be the same.")

        return cleaned


class CountryUploadForm(forms.Form):
    file = forms.FileField()
    dry_run = forms.BooleanField(required=False)
