from django import forms
from Exactus.accounts.models import User
from Exactus.company.models import ClientGroup

class EmployeeAccessForm(forms.ModelForm):
    """
    Form to manage User access (Role & Client Group) directly from the Employee Account tab.
    Restricts role selection to Client roles only.
    """
    
    # Filter roles to show only CLIENT_ROLES (Director, Manager, Specialist, Finance, Employee)
    CLIENT_ROLE_CHOICES = [
        (role_code, role_label) 
        for role_code, role_label in User.ROLE_CHOICES 
        if role_code in User.CLIENT_ROLES
    ]

    role = forms.ChoiceField(
        choices=CLIENT_ROLE_CHOICES,  # <--- Updated to use filtered list
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