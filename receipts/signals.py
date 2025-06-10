# receipts/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Receipt, PurchaseType
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Receipt)
def receipt_created_notification(sender, instance, created, **kwargs):
    """
    Send notification when a new receipt is created.
    """
    if created:
        # Log the creation
        logger.info(f"New receipt created: {instance}")
        
        # Optional: Send email notification to admin/manager
        if hasattr(settings, 'RECEIPT_NOTIFICATION_EMAIL') and settings.RECEIPT_NOTIFICATION_EMAIL:
            try:
                subject = f"New Receipt Submitted: {instance.company_name}"
                message = f"""
                A new receipt has been submitted:
                
                Date: {instance.date_of_purchase}
                Company: {instance.company_name}
                Amount: ${instance.total_amount}
                Worker: {instance.worker}
                Project: {instance.project}
                Type: {instance.purchase_type}
                
                Description: {instance.description}
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.RECEIPT_NOTIFICATION_EMAIL],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send receipt notification email: {e}")


@receiver(post_save, sender=Receipt)
def receipt_reimbursement_notification(sender, instance, **kwargs):
    """
    Send notification when a receipt is marked as reimbursed.
    """
    if instance.is_reimbursed and instance.reimbursement_date:
        # Log the reimbursement
        logger.info(f"Receipt {instance.id} marked as reimbursed on {instance.reimbursement_date}")
        
        # Optional: Send email to worker about reimbursement
        if (hasattr(settings, 'SEND_REIMBURSEMENT_NOTIFICATIONS') and 
            settings.SEND_REIMBURSEMENT_NOTIFICATIONS and 
            instance.worker and 
            hasattr(instance.worker, 'email') and 
            instance.worker.email):
            
            try:
                subject = f"Expense Reimbursement Processed: {instance.company_name}"
                message = f"""
                Hello {instance.worker.first_name},
                
                Your expense has been processed for reimbursement:
                
                Receipt Details:
                - Date: {instance.date_of_purchase}
                - Company: {instance.company_name}
                - Amount: ${instance.total_amount}
                - Project: {instance.project}
                - Reimbursement Date: {instance.reimbursement_date}
                
                Please contact HR if you have any questions.
                
                Best regards,
                Company Management
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.worker.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send reimbursement notification email: {e}")


@receiver(pre_delete, sender=PurchaseType)
def prevent_purchase_type_deletion(sender, instance, **kwargs):
    """
    Prevent deletion of purchase types that are in use.
    """
    if instance.receipts.exists():
        from django.core.exceptions import ValidationError
        raise ValidationError(
            f"Cannot delete purchase type '{instance.name}' because it is being used by {instance.receipts.count()} receipts."
        )


@receiver(post_save, sender=PurchaseType)
def log_purchase_type_changes(sender, instance, created, **kwargs):
    """
    Log when purchase types are created or modified.
    """
    if created:
        logger.info(f"New purchase type created: {instance.name} ({instance.code})")
    else:
        logger.info(f"Purchase type updated: {instance.name} ({instance.code})")


# Additional utility functions for signals
def calculate_receipt_totals_by_project(project_id):
    """
    Calculate total receipts for a specific project.
    This can be called from other parts of the application.
    """
    from django.db.models import Sum
    
    total = Receipt.objects.filter(
        project_id=project_id
    ).aggregate(
        total_amount=Sum('total_amount')
    )['total_amount'] or 0
    
    return total


def get_unreimbursed_receipts_for_worker(worker_id):
    """
    Get all unreimbursed receipts for a specific worker.
    """
    return Receipt.objects.filter(
        worker_id=worker_id,
        is_reimbursed=False
    ).order_by('-date_of_purchase')