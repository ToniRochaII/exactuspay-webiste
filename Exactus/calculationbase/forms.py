from django import forms
from Exactus.elements.models import Element
from .models import CalculationBase

class CalculationBaseForm(forms.ModelForm):
    class Meta:
        model = CalculationBase
        fields = "__all__"
        exclude = ["country", "regulations"]

    def __init__(self, *args, **kwargs):
        # 1. Extract custom arguments (country, regulations) BEFORE calling super()
        #    This prevents the "unexpected keyword argument" error.
        country = kwargs.pop("country", None)
        regulations = kwargs.pop("regulations", None)

        # 2. Call the parent class init with the cleaned kwargs
        super().__init__(*args, **kwargs)

        # 3. Apply custom filtering based on the extracted country
        if country:
            # Base queryset
            base_qs = Element.objects.filter(country=country).order_by("element_code")

            # ELEMENT should include all elements EXCEPT Base
            self.fields["element"].queryset = base_qs.exclude(
                element_categorytype="Base"
            )

            # ELEMENT BASE should include ONLY Base category
            self.fields["element_base"].queryset = base_qs.filter(
                element_categorytype="Base"
            )

            self.fields["element"].empty_label = "Select Element"
            self.fields["element_base"].empty_label = "Select Base Element"

        # 4. Apply CSS classes and attributes
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

            if name.startswith("bracket_") or name.startswith("rate_"):
                field.widget.attrs["placeholder"] = "0.000"
            
            # Helper for decimal inputs (keep them small)
            if name.endswith("_decimals"):
                field.widget.attrs["min"] = "0"
                field.widget.attrs["max"] = "10"
                field.widget.attrs["placeholder"] = "Dec"