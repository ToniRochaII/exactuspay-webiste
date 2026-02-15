from django.apps import AppConfig


class ElementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Exactus.elements'
    
    def ready(self):
        # Import signals when the app is ready to register the receivers
        import Exactus.elements.signals
