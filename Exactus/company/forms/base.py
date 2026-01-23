from django import forms
from Exactus.company.models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'trade_name', 'legal_name', 'company_code', 'company_number',
            'building_name', 'road_name_1', 'town', 'post_code',
            'tax_id_01', 'rti_user_id', 'account_status', 'logo'
        ]
        widgets = {
            'trade_name': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_code': forms.TextInput(attrs={'class': 'form-control'}),
            'company_number': forms.TextInput(attrs={'class': 'form-control'}),
            'building_name': forms.TextInput(attrs={'class': 'form-control'}),
            'road_name_1': forms.TextInput(attrs={'class': 'form-control'}),
            'town': forms.TextInput(attrs={'class': 'form-control'}),
            'post_code': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id_01': forms.TextInput(attrs={'class': 'form-control'}),
            'rti_user_id': forms.TextInput(attrs={'class': 'form-control'}),
            'account_status': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
