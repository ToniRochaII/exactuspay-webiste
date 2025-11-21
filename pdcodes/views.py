from django import forms
from .models import PDcode


class PDcodeForm(forms.ModelForm):
    """
    Form for creating/updating PD codes.
    - Excludes company (set in the view)
    - Validates that pdcode_code is unique per company
    """

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = PDcode
        exclude = ["company", "slug"]
        widgets = {
            "pdcode_status": forms.Select(attrs={"class": "form-select"}),
            "pdcode_frequency": forms.Select(attrs={"class": "form-select"}),
            "pdcode_type": forms.Select(attrs={"class": "form-select"}),
            "pdcode_class": forms.Select(attrs={"class": "form-select"}),
            "pdcode_category": forms.Select(attrs={"class": "form-select"}),
            "pdcode_categorytype": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_pdcode_code(self):
        code = self.cleaned_data.get("pdcode_code")

        # No company passed → skip custom validation (shouldn't happen in our views)
        if not self.company or not code:
            return code

        qs = PDcode.objects.filter(company=self.company, pdcode_code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "This PD Code already exists for this company."
            )

        return code
