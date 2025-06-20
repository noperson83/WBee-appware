from django.apps import AppConfig


class LocationConfig(AppConfig):
    """
    Django app configuration for the Location application.
    
    This app handles business-agnostic location management with support for:
    - Multiple business categories (Construction, Entertainment, Investigation, etc.)
    - Dynamic field choices and terminology
    - GPS coordinates and mapping
    - Document and note management
    - Related addresses and contacts
    """
    
    # Required for Django 3.2+
    default_auto_field = 'django.db.models.BigAutoField'
    
    # App name - must match the directory name
    name = 'location'
    
    # Human-readable name for the app
    verbose_name = 'Location Management'
    
    # Optional: Custom label for the app (defaults to name)
    label = 'location'
    
    def ready(self):
        """
        Called when the app is ready. Used for:
        - Importing signal handlers
        - Performing app initialization
        - Setting up any required data
        """
        try:
            # Import signal handlers if you have any
            import location.signals  # noqa F401
        except ImportError:
            pass
        
        # Initialize default business categories and choices if needed
        # This runs during Django startup, so be careful with database operations
        self.setup_default_data()
    
    def setup_default_data(self):
        """
        Set up default business categories and configurable choices.
        Only runs if the database is ready and migrated.
        """
        from django.db import connection
        from django.core.management.color import no_style
        
        try:
            # Check if migrations have been applied
            with connection.cursor() as cursor:
                # Check if our main tables exist
                tables = connection.introspection.table_names()
                required_tables = [
                    'location_businesscategory',
                    'location_configurablechoice',
                    'location_location'
                ]
                
                if all(table in tables for table in required_tables):
                    # Safe to create default data
                    from .models import create_default_business_categories
                    create_default_business_categories()
                    
        except Exception as e:
            # During migrations or initial setup, database might not be ready
            # This is normal and expected
            pass
