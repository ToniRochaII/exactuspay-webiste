from django import forms
from django.conf import settings
from Exactus.employee.models import Employee
from Exactus.accounts.models import User
from Exactus.company.models import ClientGroup

class BaseEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ["company"]
        # Remove the widgets dictionary from here to avoid inheritance confusion.
        # We will set them manually in __init__.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Define the specific date fields to target
        #    (Make sure these match your models.py exactly)
        date_fields = ['date_of_birth', 'employment_start_date', 'employment_end_date']

        for field_name in date_fields:
            if field_name in self.fields:
                field = self.fields[field_name]
                
                # 2. FORCE THE WIDGET: Override whatever the child form set
                #    This ensures type="date" is present.
                field.widget = forms.DateInput(
                    format='%Y-%m-%d',
                    attrs={'class': 'form-control', 'type': 'date'}
                )

                # 3. FORCE THE VALUE: Handle the Chrome display issue
                #    If the instance has a value, force it to a YYYY-MM-DD string.
                if self.instance and self.instance.pk:
                    val = getattr(self.instance, field_name)
                    if val:
                        self.initial[field_name] = val.strftime('%Y-%m-%d')
                
                # 4. FORCE THE VALIDATION: Accept the ISO format
                if not field.input_formats:
                    field.input_formats = settings.DATE_INPUT_FORMATS
                if '%Y-%m-%d' not in field.input_formats:
                    field.input_formats = list(field.input_formats) + ['%Y-%m-%d']

        # 5. General styling for all other fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'