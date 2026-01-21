from django import forms
from django.core.exceptions import ValidationError

from Exactus.compensation.models import CompensationComponent
from Exactus.pdcodes.models import PDcode


class CompensationComponentForm(forms.ModelForm):
    class Meta:
        model = CompensationComponent
        fields = [
            "pd_code",
            "category",
            "amount",
            "start_date",
            "end_date",
            "description",
            "reference",
            "is_active",
        ]
        widgets = {
            "pd_code": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            # --- CHANGE START: Added format='%Y-%m-%d' ---
            "start_date": forms.DateInput(
                format='%Y-%m-%d',
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                format='%Y-%m-%d',
                attrs={"class": "form-control", "type": "date"}
            ),
            # --- CHANGE END ---
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        # Floating-label friendly placeholder
        self.fields["category"].choices = [
            ("", "Select category"),
            *CompensationComponent.CATEGORY_CHOICES,
        ]

        # 🔒 PD Codes restricted to the company
        if self.company is None:
            # Safety: no company = no PD codes
            self.fields["pd_code"].queryset = PDcode.objects.none()
        else:
            self.fields["pd_code"].queryset = PDcode.objects.filter(
                company=self.company
            )

        self.fields["pd_code"].label = "Pay / Deduction Code"

        # Track original values for processed lock
        self._original_values = {}
        if self.instance and self.instance.pk:
            for name in ("pd_code", "amount", "start_date", "end_date"):
                self._original_values[name] = getattr(self.instance, name)

    def clean(self):
        cleaned = super().clean()

        category = cleaned.get("category")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        amount = cleaned.get("amount")

        if not start_date:
            raise ValidationError("Start date is required.")

        if amount is not None and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")

        if category == CompensationComponent.CATEGORY_PERMANENT:
            if end_date and end_date < start_date:
                raise ValidationError(
                    "End date cannot be before start date for permanent components."
                )

        if category == CompensationComponent.CATEGORY_VARIABLE:
            if not end_date:
                raise ValidationError("End date is required for variable components.")
            if end_date < start_date:
                raise ValidationError(
                    "End date cannot be before start date for variable components."
                )

        if self.instance.pk and self.instance.processed:
            for field, original in self._original_values.items():
                if field != "end_date" and cleaned.get(field) != original:
                    raise ValidationError(
                        "This component has already been processed in payroll. "
                        "Only the end date may be changed."
                    )

        return cleaned