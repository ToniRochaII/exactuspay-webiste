from django.apps import AppConfig


class CountryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'country'

    def ready(self):
        import country.signals
