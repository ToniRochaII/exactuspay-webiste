# Exactus/compensation/forms.py
from django import forms
from django.core.exceptions import ValidationError

from Exactus.compensation.models import CompensationComponent
from Exactus.pdcodes.models import PDcode


class CompensationComponentForm(forms.ModelForm):
    class Meta:
        model = CompensationComponent
        fields = ["pd_code", "category", "amount", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
        }

    def __init__(self, *args, company=None, **kwargs):
        """
        company: used to filter PD Codes to only those for this company.
        """
        super().__init__(*args, **kwargs)

        if company is not None:
            self.fields["pd_code"].queryset = PDcode.objects.filter(company=company)

        # Ensure Bootstrap form-control on pd_code & category
        self.fields["pd_code"].widget.attrs.setdefault("class", "form-select")
        self.fields["category"].widget.attrs.setdefault("class", "form-select")

        # Track original values to enforce the "processed can only change end_date" rule
        self._original_values = {}
        if self.instance and self.instance.pk:
            for name in ["pd_code", "category", "amount", "start_date", "end_date"]:
                self._original_values[name] = getattr(self.instance, name)

    def clean(self):
        cleaned = super().clean()

        category = cleaned.get("category")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")

        # Common: start_date required
        if not start_date:
            raise ValidationError("Start date is required.")

        # Permanent
        if category == CompensationComponent.CATEGORY_PERMANENT:
            # end_date optional but if present must be >= start_date
            if end_date and end_date < start_date:
                raise ValidationError("End date cannot be before start date for a permanent component.")

        # Variable
        if category == CompensationComponent.CATEGORY_VARIABLE:
            # They said start and end are required for variable
            if not end_date:
                raise ValidationError("End date is required for variable components.")
            if end_date < start_date:
                raise ValidationError("End date cannot be before start date for a variable component.")

        # Once processed, only end_date may change
        if self.instance and self.instance.pk and self.instance.processed:
            changed_not_allowed = []
            for name, original in self._original_values.items():
                new_value = cleaned.get(name, original)
                if name != "end_date" and new_value != original:
                    changed_not_allowed.append(name)

            if changed_not_allowed:
                raise ValidationError(
                    "This component was already processed in payroll. "
                    "Only the end date can be modified."
                )

        return cleaned
