from django import forms
from Exactus.employee.models import Compensation

class CompensationForm(forms.ModelForm):
    class Meta:
        model = Compensation
        fields = ['effective_date', 'pay_frequency', 'currency', 'amount', 'reason', 'comments']
        widgets = {
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply standard styling
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'