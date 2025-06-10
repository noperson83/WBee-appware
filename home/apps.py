# home/apps.py
"""
Clean Django 5 app configuration for home app.
No database access during initialization.
"""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """
    Configuration for the home/dashboard application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'
    verbose_name = 'Dashboard & Home'
    
    def ready(self):
        """
        Initialize the app when Django starts.
        Import signals only - no database access.
        """
        # Import signal handlers (this will connect the User post_save signal)
        try:
            from . import models  # This imports the signal receivers
        except ImportError:
            pass