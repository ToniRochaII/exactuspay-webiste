# calculationbase/forms.py
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
            # Base queryset
            base_qs = Element.objects.filter(country=country).order_by("element_code")

            # 1️⃣ ELEMENT should include all elements EXCEPT Base
            self.fields["element"].queryset = base_qs.exclude(
                element_categorytype="Base"
            )

            # 2️⃣ ELEMENT BASE should include ONLY Base category
            self.fields["element_base"].queryset = base_qs.filter(
                element_categorytype="Base"
            )

            self.fields["element"].empty_label = "Select Element"
            self.fields["element_base"].empty_label = "Select Base Element"

        # 3️⃣ Apply CSS classes (floating labels)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

            if name.startswith("bracket_") or name.startswith("rate_"):
                field.widget.attrs["placeholder"] = "0.000"
