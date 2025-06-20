# asset/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging

logger = logging.getLogger(__name__)


class AssetConfig(AppConfig):
    """
    Configuration for the asset management application.
    
    Handles company assets including equipment, vehicles, tools,
    and other physical resources with tracking, maintenance,
    and depreciation capabilities.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asset'
    verbose_name = 'Asset Management'
    
    # App-specific configuration
    default_asset_categories = [
        'Equipment', 'Vehicles', 'Tools', 'Computers', 
        'Furniture', 'Software', 'Other'
    ]
    
    def ready(self):
        """
        Initialize the app when Django starts.
        Set up signals, permissions, and default data.
        """
        # Import signal handlers
        try:
            from . import signals
        except ImportError:
            pass
        
        # Import and register any custom checks
        try:
            from . import checks
        except ImportError:
            pass
        
        # Set up post-migration signal to create default data
        post_migrate.connect(self.create_default_asset_data, sender=self)
    
    def create_default_asset_data(self, sender, **kwargs):
        """
        Create default asset categories and statuses after migrations.
        Only runs after migrations are applied.
        """
        if kwargs.get('verbosity', 1) >= 2:
            logger.info("Setting up default asset data...")
        
        try:
            # Import here to avoid AppRegistryNotReady errors
           # from .models import AssetCategory, AssetStatus
            
            # Create default asset categories
            #for category_name in self.default_asset_categories:
            #    AssetCategory.objects.get_or_create(
            #        name=category_name,
            #        defaults={
            #            'description': f'Default {category_name.lower()} category',
            #            'is_active': True
            #        }
            #    )
            
            # Create default asset statuses
            default_statuses = [
                ('Active', 'Asset is in active use', '#28a745'),
                ('Maintenance', 'Asset is under maintenance', '#ffc107'),
                ('Retired', 'Asset is retired/disposed', '#6c757d'),
                ('Lost/Stolen', 'Asset is lost or stolen', '#dc3545'),
                ('Reserved', 'Asset is reserved for future use', '#17a2b8'),
            ]
            

            #for status_name, description, color in default_statuses:
             #   AssetStatus.objects.get_or_create(
              #      name=status_name,
               #     defaults={
                #        'description': description,
                 #       'color': color,
                  #      'is_active': True
                  #  }
                #)
                
        except Exception:
            # Don't fail if models don't exist yet
            logger.exception("Could not create default asset data")
    
    @property
    def asset_depreciation_methods(self):
        """Available depreciation methods for assets."""
        return [
            ('straight_line', 'Straight Line'),
            ('declining_balance', 'Declining Balance'),
            ('units_of_production', 'Units of Production'),
            ('none', 'No Depreciation'),
        ]
    
    @property
    def default_maintenance_intervals(self):
        """Default maintenance intervals in days."""
        return {
            'Equipment': 90,    # 3 months
            'Vehicles': 180,    # 6 months
            'Tools': 365,       # 1 year
            'Computers': 180,   # 6 months
            'Furniture': 730,   # 2 years
            'Software': 365,    # 1 year
        }
