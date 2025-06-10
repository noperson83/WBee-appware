# company/apps.py - Modern App Configuration for Company Management

from django.apps import AppConfig


class CompanyConfig(AppConfig):
    """Configuration for the Company app"""
    
    # Use BigAutoField for new projects (Django 3.2+)
    default_auto_field = 'django.db.models.BigAutoField'
    
    name = 'company'
    verbose_name = 'Company Management'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        This method is called once Django has loaded all models.
        """
        # Import signal handlers
        try:
            from . import signals
        except ImportError:
            pass
        
        # Register any custom admin configurations
        try:
            from . import admin
        except ImportError:
            pass