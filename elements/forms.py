# elements/forms.py
from django import forms
from .models import Element

class ElementForm(forms.ModelForm):
    class Meta:
        model = Element
        fields = '__all__'
        exclude = ['country']  # Country is set in the view
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class ElementUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with element data'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.csv'
        })