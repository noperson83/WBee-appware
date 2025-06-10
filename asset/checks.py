# asset/checks.py
from django.core.checks import Error, Warning, register, Tags
from django.conf import settings


@register(Tags.compatibility)
def check_asset_settings(app_configs, **kwargs):
    """
    Check that asset-related settings are properly configured.
    """
    errors = []
    
    # Check for asset notification email
    if not hasattr(settings, 'ASSET_NOTIFICATION_EMAIL'):
        errors.append(
            Warning(
                'ASSET_NOTIFICATION_EMAIL setting is not configured.',
                hint='Add ASSET_NOTIFICATION_EMAIL to your settings to receive asset notifications.',
                id='asset.W001',
            )
        )
    
    # Check media configuration for asset images
    if not hasattr(settings, 'MEDIA_ROOT') or not settings.MEDIA_ROOT:
        errors.append(
            Error(
                'MEDIA_ROOT is not configured.',
                hint='Asset images require MEDIA_ROOT to be set in settings.',
                id='asset.E001',
            )
        )
    
    # Check for asset depreciation settings
    if not hasattr(settings, 'ASSET_DEPRECIATION_ENABLED'):
        errors.append(
            Warning(
                'ASSET_DEPRECIATION_ENABLED setting is not configured.',
                hint='Add ASSET_DEPRECIATION_ENABLED = True to enable asset depreciation calculations.',
                id='asset.W002',
            )
        )
    
    return errors


#@register(Tags.models)
#def check_asset_model_configuration(app_configs, **kwargs):
    """
    Check asset model configuration for common issues.
    """
#    errors = []
    
    #try:
    #    from .models import Asset, AssetCategory, AssetStatus
        
        # Check if default categories exist
    #    if not AssetCategory.objects.exists():
    #        errors.append(
    #            Warning(
    #                'No asset categories found.',
    #                hint='Run migrations and restart the server to create default categories.',
    #                id='asset.W003',
    #            )
    #        )
        
        # Check if default statuses exist
       # if not AssetStatus.objects.exists():
       #     errors.append(
       #         Warning(
       #             'No asset statuses found.',
       #             hint='Run migrations and restart the server to create default statuses.',
       #             id='asset.W004',
       #         )
       #     )
        
        # Check for assets without categories
    #    assets_without_category = Asset.objects.filter(category__isnull=True).count()
    #    if assets_without_category > 0:
    #        errors.append(
    #            Warning(
    #                f'{assets_without_category} assets have no category assigned.',
    #                hint='Assign categories to all assets for better organization.',
    #                id='asset.W005',
    #            )
    #        )
        
    #except Exception:
    #    # Models might not exist yet during initial setup
    #    pass
   # 
   # return errors


@register(Tags.security)
def check_asset_security(app_configs, **kwargs):
    """
    Check asset-related security configurations.
    """
    errors = []
    
    # Check file upload security
    if hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE'):
        max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        if max_size > 10 * 1024 * 1024:  # 10MB
            errors.append(
                Warning(
                    f'FILE_UPLOAD_MAX_MEMORY_SIZE is set to {max_size} bytes.',
                    hint='Consider limiting file upload size for security (recommended: 10MB max).',
                    id='asset.S001',
                )
            )
    
    # Check if asset images are served securely
    if hasattr(settings, 'MEDIA_URL') and settings.DEBUG:
        errors.append(
            Warning(
                'Media files are served directly by Django in DEBUG mode.',
                hint='In production, serve media files through your web server (nginx/apache).',
                id='asset.S002',
            )
        )
    
    return errors


@register(Tags.compatibility)
def check_asset_performance(app_configs, **kwargs):
    """
    Check for asset-related performance issues.
    """
    errors = []
    
    try:
        from .models import Asset
        
        # Check for large number of assets without pagination
        asset_count = Asset.objects.count()
        if asset_count > 1000:
            errors.append(
                Warning(
                    f'You have {asset_count} assets in the system.',
                    hint='Consider implementing pagination and filtering in asset views for better performance.',
                    id='asset.P001',
                )
            )
        
        # Check if database indexes are properly configured
        # This would require more complex database introspection
        
    except Exception:
        pass
    
    return errors