from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Exactus.accounts"
    verbose_name = "Accounts & Authentication"

    def ready(self):
        # Import and connect signals
        import Exactus.accounts.signals