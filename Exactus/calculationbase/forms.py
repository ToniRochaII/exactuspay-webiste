# calculationbase/forms.py
from django import forms
from Exactus.elements.models import Element
from .models import CalculationBase

class CalculationBaseForm(forms.ModelForm):
    class Meta:
        model = CalculationBase
        fields = '__all__'
        exclude = ['country', 'regulations']
    
    def __init__(self, *args, **kwargs):
        country = kwargs.pop('country', None)
        regulations = kwargs.pop('regulations', None)
        super().__init__(*args, **kwargs)
        
        if country:
            # Get ALL elements for this country (no filtering for now)
            elements = Element.objects.filter(country=country).order_by('element_code')
            
            # For both element and element_base fields, show all elements
            self.fields['element'].queryset = elements
            self.fields['element_base'].queryset = elements
            
            # Add placeholder text to explain this is temporary
            self.fields['element_base'].help_text = "Select an element to use as base (all elements shown)"
        
        # Add CSS classes for floating labels
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name.startswith('bracket_') or field_name.startswith('rate_'):
                field.widget.attrs['placeholder'] = '0.000'