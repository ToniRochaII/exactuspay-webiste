from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from Exactus.accounts.models import User, UserProfile
from Exactus.company.models import ClientGroup

User = get_user_model()



class UserRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }




class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = [
            "name", "surname", "phone_number", "address", "city", "country",
            "preferred_language", "avatar", "notify_by_email", "notify_by_sms"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "surname": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "notify_by_email": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notify_by_sms": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }




User = get_user_model()

class UserEditForm(forms.ModelForm):
    client_group = forms.ModelChoiceField(
        queryset=ClientGroup.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Assign a group for bulk company access (Managers/Directors)."
    )
    
    class Meta:
        model = User
        # ADD 'username' TO THIS LIST
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'client_group', 'is_active']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}), # Add styling for username
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

