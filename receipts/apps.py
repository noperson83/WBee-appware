# receipts/apps.py
from django.apps import AppConfig


class ReceiptsConfig(AppConfig):
    """
    Configuration for the receipts application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'receipts'
    verbose_name = 'Receipt Management'
    
    def ready(self):
        """
        Perform initialization when the app is ready.
        """
        # Import signals here to ensure they are registered
        try:
            import receipts.signals
        except ImportError:
            pass