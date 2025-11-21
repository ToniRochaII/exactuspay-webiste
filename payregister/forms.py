from django import forms
from .models import PayRegister

class PayRegisterForm(forms.ModelForm):

    class Meta:
        model = PayRegister
        fields = [
            'pd_code', 'category', 'amount',
            'start_date', 'end_date', 'entry_date'
        ]

    def clean(self):
        cleaned = super().clean()
        cat = cleaned.get('category')

        if cat == 'PERMANENT':
            if cleaned.get('entry_date'):
                raise forms.ValidationError("Permanent entries cannot have entry_date.")

        if cat == 'TEMPORARY':
            if not cleaned.get('start_date') or not cleaned.get('end_date'):
                raise forms.ValidationError("Temporary entries require start and end date.")
            if cleaned['end_date'] < cleaned['start_date']:
                raise forms.ValidationError("End date must be after start date.")

        if cat == 'VARIABLE':
            if not cleaned.get('entry_date'):
                raise forms.ValidationError("Variable entries require an entry_date.")
            if cleaned.get('start_date') or cleaned.get('end_date'):
                raise forms.ValidationError("Variable entries cannot have start/end date.")

        return cleaned
