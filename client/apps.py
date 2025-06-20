from django.apps import AppConfig


class ClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'client'
    verbose_name = 'Client Management'
    
    def ready(self):
        """Initialize app when Django starts"""
        try:
            # Import signals if you have any
            # import client.signals
            pass
        except ImportError:
            pass
