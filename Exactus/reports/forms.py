from django import forms
from Exactus.payroll.models import Payroll

class RunReportForm(forms.Form):
    start_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    payroll = forms.ModelChoiceField(
        queryset=Payroll.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All Payrolls"
    )

    def __init__(self, *args, company_id=None, report_def=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate Payroll options for this company
        if company_id:
            self.fields['payroll'].queryset = Payroll.objects.filter(company_id=company_id)

        # Hide fields if the report definition doesn't allow them
        if report_def:
            if not report_def.allow_date_range:
                self.fields['start_date'].widget = forms.HiddenInput()
                self.fields['end_date'].widget = forms.HiddenInput()
            
            if not report_def.allow_payroll_selection:
                self.fields['payroll'].widget = forms.HiddenInput()