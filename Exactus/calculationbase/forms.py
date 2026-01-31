# Exactus/calculationbase/forms.py
from django import forms
from Exactus.elements.models import Element
from .models import CalculationBase

class CalculationBaseForm(forms.ModelForm):
    class Meta:
        model = CalculationBase
        fields = "__all__"
        exclude = ["country", "regulations"]

    def __init__(self, *args, **kwargs):
        country = kwargs.pop("country", None)
        regulations = kwargs.pop("regulations", None)
        super().__init__(*args, **kwargs)

        if country:
            base_qs = Element.objects.filter(country=country).order_by("element_code")
            self.fields["element"].queryset = base_qs.exclude(element_categorytype="Base")
            self.fields["element_base"].queryset = base_qs.filter(element_categorytype="Base")
            self.fields["element"].empty_label = "Select Element"
            self.fields["element_base"].empty_label = "Select Base Element"

        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            if name.startswith("bracket_") or name.startswith("rate_"):
                field.widget.attrs["placeholder"] = "0.000"
            if name.endswith("_decimals"):
                field.widget.attrs["min"] = "0"
                field.widget.attrs["max"] = "10"
                field.widget.attrs["placeholder"] = "Dec"

class CalculationBaseUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV File",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"})
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run (Test without saving)",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )