from django import forms
from .models import ClientGroup, Company

class ClientGroupForm(forms.ModelForm):
    companies = forms.ModelMultipleChoiceField(
        queryset=Company.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
        required=False,
        help_text="Hold Ctrl (or Cmd) to select multiple companies."
    )

    class Meta:
        model = ClientGroup
        fields = ['name', 'companies']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Smith Holdings Group'}),
        }