from django import forms
from django.core.exceptions import ValidationError
from .models import PayRegister
from Exactus.employee.models import Employee
from Exactus.pdcodes.models import PDcode


class PayRegisterForm(forms.ModelForm):
    class Meta:
        model = PayRegister
        fields = ['employee', 'pd_code', 'category', 'amount', 
                 'start_date', 'end_date', 'entry_date']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'pd_code': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
            'entry_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter employees by company if provided
        if company:
            self.fields['employee'].queryset = Employee.objects.filter(company=company)
            self.fields['pd_code'].queryset = PDcode.objects.filter(company=company)
        
        # Set required based on category
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        self.fields['entry_date'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        entry_date = cleaned_data.get('entry_date')
        
        # Validation based on category
        if category == 'PERMANENT':
            if not start_date:
                self.add_error('start_date', 'Start date is required for permanent entries.')
        elif category == 'TEMPORARY':
            if not start_date:
                self.add_error('start_date', 'Start date is required for temporary entries.')
            if not end_date:
                self.add_error('end_date', 'End date is required for temporary entries.')
            if start_date and end_date and start_date > end_date:
                self.add_error('end_date', 'End date must be after start date.')
        elif category == 'VARIABLE':
            if not entry_date:
                self.add_error('entry_date', 'Entry date is required for variable entries.')
        
        return cleaned_data
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount