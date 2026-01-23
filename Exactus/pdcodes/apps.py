from django.apps import AppConfig


class PdcodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Exactus.pdcodes'

def ready(self):
        import Exactus.pdcodes.signals  # Import signals