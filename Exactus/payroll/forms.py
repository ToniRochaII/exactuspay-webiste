from django import forms
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from Exactus.payroll.models import Payroll, PayrollPeriod
from Exactus.regulations.models import Regulations

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = [
            'fiscal_year', 'regulation', 'is_historical', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'fiscal_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
        }

    def __init__(self, country=None, company=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Attach context to the instance immediately
        if company:
            self.instance.company = company
        
        if country:
            self.instance.country = country
            self.fields['regulation'].queryset = Regulations.objects.filter(
                country=country,
                archive='N'
            ).order_by('-fiscal_year')
        else:
            self.fields['regulation'].queryset = Regulations.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        fiscal_year = cleaned_data.get('fiscal_year')
        is_historical = cleaned_data.get('is_historical')
        
        if fiscal_year:
            from django.utils import timezone
            current_year = timezone.now().year
            
            # Lower limit for historical data
            min_year = 1900 if is_historical else 2000
            
            if fiscal_year < min_year or fiscal_year > current_year + 5:
                raise forms.ValidationError({
                    'fiscal_year': f'Fiscal year must be between {min_year} and {current_year + 5}'
                })
        
        return cleaned_data

    def get_success_url(self):
        return reverse_lazy(
            "payroll:payroll_detail",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "pk": self.object.pk,
            },
        )


class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = [
            'period_number', 'name', 'frequency',
            'start_date', 'end_date', 'processing_date', 'payment_date',
            'apply_regulations', 'is_additional', 'regulation_overrides'
        ]
        widgets = {
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            # FIX: Added format='%Y-%m-%d' to all DateInputs
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'processing_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'payment_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'regulation_overrides': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter JSON overrides (e.g., {"tax_rate": 0.15})'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.payroll = kwargs.pop('payroll', None)
        super().__init__(*args, **kwargs)
        
        # Set initial period number if not provided
        if not self.instance.pk and not self.initial.get('period_number') and self.payroll:
            last_period = PayrollPeriod.objects.filter(payroll=self.payroll).order_by('period_number').last()
            if last_period:
                self.initial['period_number'] = last_period.period_number + 1
            else:
                self.initial['period_number'] = 1
        
        # Disable fields for non-editable periods
        if self.instance and self.instance.pk and not self.instance.is_editable:
            for field in self.fields:
                self.fields[field].disabled = True
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate dates
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        processing_date = cleaned_data.get('processing_date')
        is_additional = cleaned_data.get('is_additional')
        
        if start_date and end_date:
            if start_date >= end_date:
                self.add_error('end_date', 'End date must be after start date')
            
            if processing_date and processing_date > end_date:
                self.add_error('processing_date', 'Processing date must be on or after end date')
            
            # Check overlaps (skipping if additional run)
            if not is_additional:
                if self.payroll and self.instance.pk:
                    overlapping = PayrollPeriod.objects.filter(
                        payroll=self.payroll,
                        start_date__lt=end_date,
                        end_date__gt=start_date,
                        is_additional=False
                    ).exclude(pk=self.instance.pk)
                
                elif self.payroll and not self.instance.pk:
                    overlapping = PayrollPeriod.objects.filter(
                        payroll=self.payroll,
                        start_date__lt=end_date,
                        end_date__gt=start_date,
                        is_additional=False
                    )
                else:
                    overlapping = PayrollPeriod.objects.none()

                if overlapping.exists():
                    self.add_error('start_date', 'This period overlaps with an existing period')
                    self.add_error('end_date', 'This period overlaps with an existing period')
        
        period_number = cleaned_data.get('period_number')
        if period_number and period_number < 1:
            self.add_error('period_number', 'Period number must be at least 1')
        
        regulation_overrides = cleaned_data.get('regulation_overrides')
        if regulation_overrides and regulation_overrides.strip():
            try:
                import json
                json.loads(regulation_overrides)
            except json.JSONDecodeError:
                self.add_error('regulation_overrides', 'Must be valid JSON format')
        
        return cleaned_data


class PayrollProcessForm(forms.Form):
    """Form for processing a payroll period"""
    force_recalculation = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Recalculate even if already processed'
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Test calculation without saving results'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Notes about this processing run'
    )

class HistoricalUploadForm(forms.Form):
    """Form to upload historical payroll data via CSV"""
    file = forms.FileField(
        label="Upload Gross to Net Report (CSV)",
        help_text="Upload a CSV file containing historical data. Column headers must correspond to Element codes or PD codes. Must include an 'Employee ID' or 'Employee Code' column.",
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )