# asset/signals.py - FIXED VERSION
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender='asset.Asset')
def asset_pre_save(sender, instance, **kwargs):
    """
    Handle asset changes before saving.
    Track status changes and validate data.
    """
    # If this is an update (not creation)
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            
            # Track status changes
            if old_instance.status != instance.status:
                logger.info(f"Asset {instance.asset_number} status changed from {old_instance.status} to {instance.status}")
                
                # Create status change log entry (if you have this model)
                # from .models import AssetStatusLog
                # AssetStatusLog.objects.create(
                #     asset=instance,
                #     old_status=old_instance.status,
                #     new_status=instance.status,
                #     changed_by=getattr(instance, '_changed_by', None),
                #     notes=getattr(instance, '_status_change_notes', ''),
                # )
            
            # Track location changes
            if old_instance.location_status != instance.location_status:
                logger.info(f"Asset {instance.asset_number} moved from {old_instance.location_status} to {instance.location_status}")
                
                # Create location change log (if you have this model)
                # from .models import AssetLocationLog
                # AssetLocationLog.objects.create(
                #     asset=instance,
                #     old_location=old_instance.location_status,
                #     new_location=instance.location_status,
                #     changed_by=getattr(instance, '_changed_by', None),
                #     notes=getattr(instance, '_location_change_notes', ''),
                # )
                
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='asset.Asset')
def asset_post_save(sender, instance, created, **kwargs):
    """
    Handle asset actions after saving.
    Send notifications and create maintenance schedules.
    """
    if created:
        logger.info(f"New asset created: {instance.asset_number} - {instance.name}")
        
        # Send notification to asset managers
        send_asset_notification(
            subject=f"New Asset Added: {instance.name}",
            message=f"""
            A new asset has been added to the system:
            
            Asset Number: {instance.asset_number}
            Name: {instance.name}
            Category: {instance.category}
            Status: {instance.status}
            Purchase Date: {instance.purchase_date}
            Cost: ${instance.purchase_price}
            
            Please review and assign if necessary.
            """,
            asset=instance
        )
        
        # Create initial maintenance schedule if applicable
        create_maintenance_schedule(instance)
    
    else:
        # Check if asset needs maintenance reminder
        check_maintenance_due(instance)


@receiver(post_delete, sender='asset.Asset')
def asset_post_delete(sender, instance, **kwargs):
    """
    Handle asset deletion.
    Log the deletion and clean up related data.
    """
    logger.warning(f"Asset deleted: {instance.asset_number} - {instance.name}")
    
    # Send deletion notification
    send_asset_notification(
        subject=f"Asset Deleted: {instance.name}",
        message=f"""
        An asset has been deleted from the system:
        
        Asset Number: {instance.asset_number}
        Name: {instance.name}
        Last Status: {instance.status}
        
        This action cannot be undone.
        """,
        asset=instance
    )


# FIXED: Changed from 'asset.MaintenanceRecord' to 'asset.AssetMaintenanceRecord'
@receiver(post_save, sender='asset.AssetMaintenanceRecord')
def maintenance_record_created(sender, instance, created, **kwargs):
    """
    Handle maintenance record creation.
    Update asset status and schedule next maintenance.
    """
    if created:
        logger.info(f"Maintenance record created for asset {instance.asset.asset_number}")
        
        # Update asset's last maintenance date
        instance.asset.last_maintenance_date = instance.performed_date
        instance.asset.save(update_fields=['last_maintenance_date'])
        
        # Schedule next maintenance if this was completed maintenance
        if instance.maintenance_type in ['scheduled', 'preventive']:
            schedule_next_maintenance(instance.asset, instance.performed_date)


def send_asset_notification(subject, message, asset=None):
    """
    Send email notification about asset changes.
    """
    if not hasattr(settings, 'ASSET_NOTIFICATION_EMAIL'):
        return
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ASSET_NOTIFICATION_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send asset notification: {e}")


def create_maintenance_schedule(asset):
    """
    Create initial maintenance schedule for new assets.
    """
    try:
        # Check if asset category requires maintenance
        if asset.category and asset.category.requires_maintenance:
            from .models import AssetMaintenanceRecord
            
            # Calculate next maintenance date
            interval_days = asset.category.default_maintenance_interval_days or 90
            next_maintenance = timezone.now().date() + timedelta(days=interval_days)
            
            # Update asset's next maintenance date
            asset.next_maintenance_date = next_maintenance
            asset.save(update_fields=['next_maintenance_date'])
            
            logger.info(f"Maintenance schedule created for {asset.asset_number} - next maintenance: {next_maintenance}")
        
    except Exception as e:
        logger.error(f"Failed to create maintenance schedule for {asset.asset_number}: {e}")


def schedule_next_maintenance(asset, last_maintenance_date):
    """
    Schedule the next maintenance based on the last completed maintenance.
    """
    try:
        if asset.category and asset.category.requires_maintenance:
            interval_days = asset.category.default_maintenance_interval_days or 90
            next_maintenance = last_maintenance_date + timedelta(days=interval_days)
            
            # Update asset's next maintenance date
            asset.next_maintenance_date = next_maintenance
            asset.save(update_fields=['next_maintenance_date'])
            
            logger.info(f"Next maintenance scheduled for {asset.asset_number}: {next_maintenance}")
        
    except Exception as e:
        logger.error(f"Failed to schedule next maintenance for {asset.asset_number}: {e}")


def check_maintenance_due(asset):
    """
    Check if asset has overdue maintenance and send reminders.
    """
    try:
        if asset.next_maintenance_date and asset.next_maintenance_date < timezone.now().date():
            send_asset_notification(
                subject=f"Asset Maintenance Overdue: {asset.name}",
                message=f"""
                Asset {asset.asset_number} - {asset.name} has overdue maintenance:
                
                Scheduled maintenance date: {asset.next_maintenance_date}
                Days overdue: {(timezone.now().date() - asset.next_maintenance_date).days}
                
                Please schedule maintenance as soon as possible.
                """,
                asset=asset
            )
            
    except Exception as e:
        logger.error(f"Failed to check maintenance for {asset.asset_number}: {e}")


# Utility functions for external use
def bulk_update_asset_status(asset_ids, new_status, changed_by=None, notes=''):
    """
    Bulk update multiple assets' status.
    """
    from .models import Asset
    
    assets = Asset.objects.filter(id__in=asset_ids)
    updated_count = 0
    
    for asset in assets:
        asset._changed_by = changed_by
        asset._status_change_notes = notes
        asset.status = new_status
        asset.save()
        updated_count += 1
    
    logger.info(f"Bulk updated {updated_count} assets to status: {new_status}")
    return updated_count


def generate_asset_reports():
    """
    Generate periodic asset reports.
    Can be called from management commands or scheduled tasks.
    """
    from .models import Asset
    from django.db import models
    
    # Assets by status
    status_report = Asset.objects.values('status').annotate(
        count=models.Count('id')
    )
    
    # Assets needing maintenance
    maintenance_due = Asset.objects.filter(
        next_maintenance_date__lt=timezone.now().date(),
        is_active=True
    ).count()
    
    # Assets by condition
    condition_report = Asset.objects.values('condition').annotate(
        count=models.Count('id')
    )
    
    # High value assets
    high_value_assets = Asset.objects.filter(
        purchase_price__gt=10000,
        is_active=True
    ).count()
    
    report_data = {
        'status_breakdown': list(status_report),
        'condition_breakdown': list(condition_report),
        'maintenance_due_count': maintenance_due,
        'high_value_assets': high_value_assets,
        'generated_at': timezone.now(),
    }
    
    logger.info(f"Asset report generated: {report_data}")
    return report_data
