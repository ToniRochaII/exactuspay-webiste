from django import forms
from .models import PayRegister
from pdcodes.models import PDcode   # ✅ IMPORT THIS


class PayRegisterForm(forms.ModelForm):
    class Meta:
        model = PayRegister
        fields = [
            "pd_code",
            "category",
            "amount",
            "start_date",
            "end_date",
            "entry_date",
        ]


    def __init__(self, *args, **kwargs):
        # We will filter by company, which implicitly filters by country
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)


    def clean(self):
        cleaned = super().clean()
        cat = cleaned.get("category")

        # Your existing validation logic (unchanged)
        if cat in ["PERMANENT", "TEMPORARY"]:
            if not cleaned.get("start_date"):
                raise forms.ValidationError("Permanent/Temporary entries require a start_date.")
            if not cleaned.get("end_date") and cat == "TEMPORARY":
                raise forms.ValidationError("Temporary entries require an end_date.")
            if cleaned.get("start_date") and cleaned.get("end_date"):
                if cleaned["end_date"] < cleaned["start_date"]:
                    raise forms.ValidationError("End date must be after start date.")

        if cat == "VARIABLE":
            if not cleaned.get("entry_date"):
                raise forms.ValidationError("Variable entries require an entry_date.")
            if cleaned.get("start_date") or cleaned.get("end_date"):
                raise forms.ValidationError("Variable entries cannot have start/end date.")

        return cleaned

class PayRegisterUploadForm(forms.Form):
    file = forms.FileField(label="CSV File")
    dry_run = forms.BooleanField(required=False, initial=False, help_text="Validate only, do not save.")
