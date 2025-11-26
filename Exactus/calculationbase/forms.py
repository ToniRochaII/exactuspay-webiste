from django import forms
from Exactus.elements.models import Element
from Exactus.calculationbase.models import CalculationBase

class CalculationBaseForm(forms.ModelForm):
    class Meta:
        model = CalculationBase
        exclude = ["country", "regulations"]  # We set these in the view
        widgets = {
            "element": forms.Select(attrs={"class": "form-select"}),
            "element_base": forms.Select(attrs={"class": "form-select"}),
            "tax_jurisdiction": forms.TextInput(attrs={"class": "form-control"}),
            "table_type": forms.Select(attrs={"class": "form-select"}),
            "ss_category": forms.Select(attrs={"class": "form-select"}),
            "base_frequency": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        country = kwargs.pop("country", None)
        regulations = kwargs.pop("regulations", None)
        super().__init__(*args, **kwargs)

        # Apply bootstrap styling
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-control")

        if country:
            self.fields["element"].queryset = Element.objects.filter(country=country)
            self.fields["element_base"].queryset = Element.objects.filter(country=country)
