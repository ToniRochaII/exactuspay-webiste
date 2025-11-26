from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Exactus.accounts"

    def ready(self):
        import accounts.signals  # ✅ safer explicit import
