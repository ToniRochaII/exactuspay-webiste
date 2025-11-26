from django import forms
from .models import Payroll
from regulations.models import Regulations

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['regulations', 'payroll_frequency']
        widgets = {
            'regulations': forms.Select(attrs={'class': 'form-select'}),
            'payroll_frequency': forms.Select(attrs={'class': 'form-select'}),
        }