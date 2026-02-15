from django import forms
from django.contrib.auth import get_user_model
from Exactus.company.models import Company, ClientGroup

User = get_user_model()

# -------------------------------------------------------------------------
# UPLOAD FORM
# -------------------------------------------------------------------------
class CompanyUploadForm(forms.Form):
    # FIXED: Renamed from 'file' to 'csv_file' to match the template
    csv_file = forms.FileField(  
        label="CSV File",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
        required=True
    )
    
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run (Test without saving)",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Check this box to validate the CSV data without saving changes to the database."
    )

# -------------------------------------------------------------------------
# STANDARD FORMS
# -------------------------------------------------------------------------
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = "__all__"
        widgets = {
            'country': forms.HiddenInput(),
        }

class ClientGroupForm(forms.ModelForm):
    class Meta:
        model = ClientGroup
        fields = ["name", "description"]



class UserAllocationForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Select User",
        widget=forms.Select(attrs={"class": "form-control select2"})
    )
    
    role = forms.ChoiceField(
        choices=[
            ("DIRECTOR", "Director"),
            ("MANAGER", "Manager"),
            ("SPECIALIST", "Specialist"),
            ("FINANCE", "Finance"),
            ("VIEWER", "Read Only"),
        ],
        label="Assign Role",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    # Assignment Type Selector
    assign_type = forms.ChoiceField(
        choices=[("COMPANY", "Single Company"), ("GROUP", "Client Group")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input", "onclick": "toggleAssignmentType(this.value)"}),
        initial="COMPANY"
    )

    company = forms.ModelChoiceField(
        queryset=Company.objects.all().order_by('trade_name'),
        required=False,
        label="Company",
        widget=forms.Select(attrs={"class": "form-control select2"})
    )

    client_group = forms.ModelChoiceField(
        queryset=ClientGroup.objects.all(),
        required=False,
        label="Client Group",
        widget=forms.Select(attrs={"class": "form-control select2"})
    )

    def clean(self):
        cleaned_data = super().clean()
        assign_type = cleaned_data.get("assign_type")
        company = cleaned_data.get("company")
        group = cleaned_data.get("client_group")

        if assign_type == "COMPANY" and not company:
            self.add_error("company", "Please select a company.")
        if assign_type == "GROUP" and not group:
            self.add_error("client_group", "Please select a client group.")


            