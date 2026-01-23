# elements/forms.py
from django import forms
from Exactus.elements.models import Element



class ElementForm(forms.ModelForm):

    sync_pdcodes = forms.BooleanField(
        required=False,
        initial=False,
        label="Update/Overwrite Linked PD Codes",
        help_text="Check this to propagate these changes to all Companies (Only for codes 1000-4900).",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Element
        fields = [
            "element_code",
            "element_name",
            "element_description",
            "element_status",
            "element_frequency",
            "element_type",
            "element_class",
            "element_category",
            "element_categorytype",
            "element_account",
            "element_map_code",
            "element_gl_account",
            "element_taxable",
            "element_tax_flat",
            "element_tax_irregular",
            "element_social_securitable",
            "element_pensionable",
            "element_payable",
            "element_calculate",
            "sync_pdcodes"
        ]
        widgets = {
            # normal text/select widgets
            "element_code": forms.TextInput(attrs={"class": "form-control"}),
            "element_name": forms.TextInput(attrs={"class": "form-control"}),
            "element_description": forms.TextInput(attrs={"class": "form-control"}),
            "element_status": forms.Select(attrs={"class": "form-select"}),
            "element_frequency": forms.Select(attrs={"class": "form-select"}),
            "element_type": forms.Select(attrs={"class": "form-select"}),
            "element_class": forms.Select(attrs={"class": "form-select"}),
            "element_category": forms.Select(attrs={"class": "form-select"}),
            "element_categorytype": forms.Select(attrs={"class": "form-select"}),
            "element_account": forms.TextInput(attrs={"class": "form-control"}),
            "element_map_code": forms.TextInput(attrs={"class": "form-control"}),
            "element_gl_account": forms.TextInput(attrs={"class": "form-control"}),

            # ✅ BOOLEAN FIELDS: must be CheckboxInput with `form-check-input`
            "element_taxable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "element_tax_flat": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "element_tax_irregular": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "element_social_securitable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "element_pensionable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "element_payable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "element_calculate": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sync_pdcodes": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }



class ElementUploadForm(forms.Form):
    """
    Form used for uploading the Elements CSV.

    IMPORTANT:
    - Field name is `csv_file` (this must match the view and template).
    """

    csv_file = forms.FileField(
        label="CSV File",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".csv",
            }
        ),
    )

    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry run (validate only)",
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure consistent styling if needed
        self.fields["csv_file"].widget.attrs.setdefault("class", "form-control")
        self.fields["dry_run"].widget.attrs.setdefault("class", "form-check-input")
