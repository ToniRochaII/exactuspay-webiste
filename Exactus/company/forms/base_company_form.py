# Exactus/company/forms/base_company_form.py

from django import forms
from Exactus.company.models import Company

class BaseCompanyForm(forms.ModelForm):
    """
    Base form for all Company interactions. 
    Specific countries should inherit from this and override __init__ or clean methods.
    """
    
    def __init__(self, *args, **kwargs):
        # Safely pop 'country' to ensure compatibility with views that pass it
        self.country_instance = kwargs.pop("country", None)
        super().__init__(*args, **kwargs)
        
        # Apply generic styling to all fields
        for field_name, field in self.fields.items():
            # Add Bootstrap classes or generic attributes here
            if hasattr(field.widget, 'input_type') and field.widget.input_type != 'checkbox':
                field.widget.attrs.setdefault('class', 'form-control')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')

            # Optional: Add data-attributes for frontend grouping if needed
            self._apply_section_attributes(field_name, field)

    def _apply_section_attributes(self, field_name, field):
        """Helper to tag fields for frontend grouping (Tabs/Sections)"""
        if field_name.startswith('bank_'):
            field.widget.attrs['data-section'] = 'banking'
        elif field_name.startswith('tax_id_'):
            field.widget.attrs['data-section'] = 'tax'
        elif field_name.startswith('government_id_'):
            field.widget.attrs['data-section'] = 'government'
        elif field_name in ['building_name', 'road_name_1', 'road_name_2', 'town', 'county', 'post_code']:
            field.widget.attrs['data-section'] = 'address'

    class Meta:
        model = Company
        exclude = ["country", "company_id"]