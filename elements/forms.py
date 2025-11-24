# elements/forms.py
from django import forms
from .models import Element


class ElementForm(forms.ModelForm):
    class Meta:
        model = Element
        fields = "__all__"
        exclude = ["country"]  # Country is set in the view

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_classes + " form-control").strip()


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
