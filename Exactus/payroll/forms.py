# Exactus/payroll/forms.py
from django import forms
from django.urls import reverse_lazy
from django.utils import timezone
from Exactus.payroll.models import Payroll, PayrollPeriod
from Exactus.regulations.models import Regulations


class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = [
            'fiscal_year', 'regulation', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'fiscal_year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
        }

    def __init__(self, country=None, company=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Attach context to the instance immediately
        # This ensures self.company exists when model.clean() runs
        if company:
            self.instance.company = company
        
        if country:
            self.instance.country = country
            
            # Filter Regulation dropdown
            self.fields['regulation'].queryset = Regulations.objects.filter(
                country=country,
                archive='N'
            ).order_by('-fiscal_year')
        else:
            self.fields['regulation'].queryset = Regulations.objects.none()


    def clean(self):
        cleaned_data = super().clean()
        fiscal_year = cleaned_data.get('fiscal_year')
        
        # Check if fiscal year is valid
        if fiscal_year:
            from django.utils import timezone
            current_year = timezone.now().year
            if fiscal_year < 2000 or fiscal_year > current_year + 5:
                raise forms.ValidationError({
                    'fiscal_year': f'Fiscal year must be between 2000 and {current_year + 5}'
                })
        
        return cleaned_data
    def get_success_url(self):
        # We need to manually construct the reverse URL using the kwargs
        # passed into the view (country_slug, company_id)
        # and the primary key of the newly created object (self.object.pk)
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
            'period_number', 'name',
            'start_date', 'end_date', 'processing_date', 'payment_date',
            'apply_regulations', 'is_additional', 'regulation_overrides'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'processing_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
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
            
            # --- FIXED LOGIC START ---
            # Only check for overlaps if this is NOT an additional run.
            if not is_additional:
                if self.payroll and self.instance.pk:
                    overlapping = PayrollPeriod.objects.filter(
                        payroll=self.payroll,
                        start_date__lt=end_date,
                        end_date__gt=start_date,
                        is_additional=False  # Only check against other normal runs
                    ).exclude(pk=self.instance.pk)
                
                elif self.payroll and not self.instance.pk:
                    # For new periods, check overlaps
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
            # --- FIXED LOGIC END (Redundant block removed) ---
        
        # Validate period number
        period_number = cleaned_data.get('period_number')
        if period_number and period_number < 1:
            self.add_error('period_number', 'Period number must be at least 1')
        
        # Validate regulation_overrides is valid JSON
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