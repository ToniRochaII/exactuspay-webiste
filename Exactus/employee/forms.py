from django import forms
from django.core.exceptions import ValidationError
from Exactus.employee.models import Employee
from Exactus.accounts.models import User
from Exactus.company.models import ClientGroup

class BaseEmployeeForm(forms.ModelForm):
    # ... (Keep your existing BaseEmployeeForm code exactly as is) ...
    class Meta:
        model = Employee
        exclude = ["company"]
    # ... (existing widgets and init) ...

class EmployeeAccessForm(forms.ModelForm):
    """
    Form to manage User access (Role & Client Group) directly from the Employee Account tab.
    """
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_role_access'}),
        label="System Role"
    )
    
    client_group = forms.ModelChoiceField(
        queryset=ClientGroup.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Client Group (Bulk Access)",
        help_text="Required if promoting to Manager or Director (Client Access)."
    )
    
    is_active = forms.BooleanField(
        required=False, 
        label="Login Enabled",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['role', 'client_group', 'is_active']

class EmployeeUploadForm(forms.Form):
    file = forms.FileField()
    dry_run = forms.BooleanField(required=False)