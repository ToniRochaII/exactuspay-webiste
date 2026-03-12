from django import forms
from django.contrib.auth import get_user_model
from Exactus.company.models import ClientGroup

User = get_user_model()

class EmployeeAccessForm(forms.ModelForm):
    """
    Edita permissões e estado do utilizador do portal para um Employee.
    Ajusta os fields se o teu User model tiver nomes diferentes.
    """
    class Meta:
        model = User
        fields = ["role", "client_group", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # role choices (se existir)
        if "role" in self.fields and hasattr(User, "ROLE_CHOICES") and hasattr(User, "CLIENT_ROLES"):
            allowed = set(User.CLIENT_ROLES)
            self.fields["role"].choices = [
                (code, label) for code, label in User.ROLE_CHOICES if code in allowed
            ]

        # client_group queryset (se existir)
        if "client_group" in self.fields:
            self.fields["client_group"].queryset = ClientGroup.objects.all()

        # widgets bootstrap
        for name, field in self.fields.items():
            if hasattr(field.widget, "attrs"):
                field.widget.attrs.setdefault("class", "form-select" if field.widget.__class__.__name__.lower().endswith("select") else "form-control")