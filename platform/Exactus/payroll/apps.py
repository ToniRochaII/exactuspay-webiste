# Exactus/payroll/apps.py
from django.apps import AppConfig

class PayrollConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Exactus.payroll'
    verbose_name = 'Payroll Management'
    
    def ready(self):
        """
        Import signals when the app is ready.
        """
        # Import signals module to connect signals
        try:
            import Exactus.payroll.signals
            # You could also explicitly connect signals here if needed
            # Exactus.payroll.signals.connect_all_signals()
        except ImportError:
            pass  # Signals module doesn't exist yet