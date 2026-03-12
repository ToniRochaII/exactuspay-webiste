# Exactus/reports/forms.py
from django import forms
from .models import ReportType, ReportLayout, ReportConfiguration

class ReportTypeForm(forms.ModelForm):
    class Meta:
        model = ReportType
        fields = ['category', 'name', 'code', 'description', 'is_statutory']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ReportLayoutForm(forms.ModelForm):
    class Meta:
        model = ReportLayout
        fields = ['report_type', 'name', 'template_file']

class ReportConfigForm(forms.ModelForm):
    class Meta:
        model = ReportConfiguration
        fields = ['report_type', 'selected_layout', 'country', 'company']
        help_texts = {
            'country': 'Leave blank for a Global System Default.',
            'company': 'Leave blank for a Country or System Default.',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company")
        country = cleaned_data.get("country")
        
        # Validation: Cannot have both Company and Country (Keep it strictly hierarchical)
        # Or allow it, but warn. For now, we follow your model logic.
        return cleaned_data