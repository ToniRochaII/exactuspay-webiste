from django import forms
from Exactus.company.models import Company

BANK_FIELD_LABELS = {
    "bank_01": "Bank Name",
    "bank_02": "Branch / Agency",
    "bank_03": "Account Number",
    "bank_04": "Account Digit",
    "bank_05": "Account Type",
    "bank_06": "PIX Key",
    "bank_07": "IBAN",
    "bank_08": "SWIFT / BIC",
}

class CompanyForm(forms.ModelForm):
    
    class Meta:
        model = Company
        exclude = ("company_id",)
        widgets = {
            "account_status": forms.Select(attrs={"class": "form-select"}),
            "account_archive": forms.Select(attrs={"class": "form-select"}),
            "country": forms.Select(attrs={"class": "form-select"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # bootstrap classes for all
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get("class", "")

            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            elif isinstance(widget, (forms.CheckboxInput,)):
                css = "form-check-input"
            elif isinstance(widget, (forms.ClearableFileInput, forms.FileInput)):
                css = "form-control"
            else:
                css = "form-control"

            widget.attrs["class"] = (existing + " " + css).strip()

        # Apply banking labels + placeholders
        for fname, label in BANK_FIELD_LABELS.items():
            if fname in self.fields:
                self.fields[fname].label = label
                self.fields[fname].required = False
                self.fields[fname].widget.attrs.setdefault("placeholder", label)
