from django.apps import AppConfig

class PdcodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Exactus.pdcodes'

def ready(self):
        # This line is REQUIRED for the automation to run
        import Exactus.pdcodes.signals