from __future__ import annotations

from django import forms

from .models import DemoRequest


class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = [
            "first_name",
            "last_name",
            "email",
            "company",
            "employees",
            "region",
        ]

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_company(self):
        return self.cleaned_data["company"].strip()

    def clean_region(self):
        return self.cleaned_data.get("region", "").strip() or "Not sure yet"
