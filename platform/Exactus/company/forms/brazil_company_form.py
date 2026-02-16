from django import forms
from django.core.exceptions import ValidationError
from Exactus.company.forms.base_company_form import BaseCompanyForm
import re

class BrazilCompanyForm(BaseCompanyForm):
    """
    Brazil Specific Company Form.
    Mapped into model slots:
      tax_id_01 = CNPJ
      tax_id_02 = Registration Date (stored as YYYY-MM-DD string)
      tax_id_03 = Primary CNAE
      tax_id_04 = Secondary CNAE
      tax_id_05 = Business Type Code
    """

    # ─────────────────────────────────────────────
    # TAB: TAXATION
    # ─────────────────────────────────────────────

    cnpj = forms.CharField(
        label="CNPJ",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "00.000.000/0001-00",
            "data-mask": "00.000.000/0001-00",
            "data-section": "tax"
        })
    )

    registration_date = forms.DateField(
        label="Registration Date",
        required=False,
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "data-section": "tax",
        })
    )

    primary_cnae = forms.CharField(
        label="Primary Economical Registration Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    secondary_cnae = forms.CharField(
        label="Secondary Economical Registration",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    business_type_code = forms.CharField(
        label="Business Type Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    # ─────────────────────────────────────────────
    # TAB: AGENT SETTINGS (RTI/Agent)
    # ─────────────────────────────────────────────

    agent_full_name = forms.CharField(
        label="Contact Full Name",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_road_name_1 = forms.CharField(
        label="Road Name",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_road_name_2 = forms.CharField(
        label="Road Name line 2",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_town = forms.CharField(
        label="Town",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )
    agent_post_code = forms.CharField(
        label="Post Code",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "data-section": "tax"})
    )

    class Meta(BaseCompanyForm.Meta):
        labels = {
            **BaseCompanyForm.Meta.labels,

            "company_code": "Company Code",
            "company_number": "Company Number",
            "trade_name": "Business Trade Name",
            "legal_name": "Legal Trade Name",

            "contact": "Contact",
            "phone": "Telephone",
            "email": "eMail",
            "website": "Website",

            "building_name": "Building Name",
            "road_name_1": "Road Name",
            "road_name_2": "Road Name line 2",
            "town": "Town",
            "post_code": "Post Code",
            "county": "County",
        }

        widgets = {
            **BaseCompanyForm.Meta.widgets,

            "company_code": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "company_number": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control", "data-section": "details"}),

            "contact": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "data-section": "communication"}),
            "website": forms.URLInput(attrs={"class": "form-control", "data-section": "communication"}),

            "building_name": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "road_name_1": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "road_name_2": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "town": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "post_code": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),
            "county": forms.TextInput(attrs={"class": "form-control", "data-section": "communication"}),

            # ensure these look right in your Account tab
            "account_status": forms.Select(attrs={"class": "form-select", "data-section": "account"}),
            "account_archive": forms.Select(attrs={"class": "form-select", "data-section": "account"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ 1) Hydrate Brazil proxy fields from stored tax_id slots
        if self.instance and getattr(self.instance, "pk", None):
            self.fields["cnpj"].initial = self.instance.tax_id_01 or ""

            raw_date = (self.instance.tax_id_02 or "").strip()
            if raw_date:
                try:
                    self.fields["registration_date"].initial = forms.DateField().to_python(raw_date)
                except Exception:
                    self.fields["registration_date"].initial = None

            self.fields["primary_cnae"].initial = self.instance.tax_id_03 or ""
            self.fields["secondary_cnae"].initial = self.instance.tax_id_04 or ""
            self.fields["business_type_code"].initial = self.instance.tax_id_05 or ""

        # ✅ 2) Hide the generic tax_id_* fields to avoid duplicates in template
        # BUT DO NOT hide bank_* because you want the banking tab visible.
        for name, field in self.fields.items():
            if name.startswith("tax_id_"):
                field.widget = forms.HiddenInput()

        # ✅ 3) Apply bootstrap classes to anything not already styled
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = (existing + " form-select").strip()
            elif isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs["class"] = (existing + " form-check-input").strip()
            elif not isinstance(widget, (forms.FileInput, forms.ClearableFileInput)):
                widget.attrs["class"] = (existing + " form-control").strip()

    def clean_cnpj(self):
        raw = (self.cleaned_data.get("cnpj") or "").strip()
        digits = re.sub(r"\D", "", raw)
        if len(digits) != 14:
            raise ValidationError("CNPJ must be exactly 14 digits.")
        return raw  # preserve formatting

    def clean(self):
        cleaned = super().clean()

        # ✅ store date into model slot as ISO string
        reg_date = cleaned.get("registration_date")
        cleaned["tax_id_02"] = reg_date.isoformat() if reg_date else ""

        return cleaned

    def save(self, commit=True):
        company = super().save(commit=False)

        # ✅ Map Brazil fields back into tax slots
        company.tax_id_01 = self.cleaned_data.get("cnpj", "") or ""
        company.tax_id_02 = self.cleaned_data.get("tax_id_02", "") or ""  # set by clean()
        company.tax_id_03 = self.cleaned_data.get("primary_cnae", "") or ""
        company.tax_id_04 = self.cleaned_data.get("secondary_cnae", "") or ""
        company.tax_id_05 = self.cleaned_data.get("business_type_code", "") or ""

        if commit:
            company.save()
            self.save_m2m()

        return company
