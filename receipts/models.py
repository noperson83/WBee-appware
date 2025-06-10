from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from decimal import Decimal
from hr.models import Worker
from project.models import Project

# Shared abstract base models
from client.models import TimeStampedModel


class PurchaseType(TimeStampedModel):
    """
    Model representing different types of purchases that can be customized per company.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text='Name of the purchase type (e.g., Air Fair, Equipment, Meals)'
    )
    code = models.CharField(
        max_length=10, 
        unique=True,
        help_text='Short code for the purchase type (e.g., AF, EQ, ML)'
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description of what this purchase type covers'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this purchase type is currently available for selection'
    )
    # Timestamps provided by TimeStampedModel

    class Meta:
        ordering = ['name']
        verbose_name = 'Purchase Type'
        verbose_name_plural = 'Purchase Types'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Receipt(TimeStampedModel):
    """
    Model representing a receipt for expense tracking.
    Updated for Django 5 with modern best practices.
    """
    # Core receipt information
    date_of_purchase = models.DateField(
        help_text='Date of purchase (YYYY-MM-DD format)'
    )
    company_name = models.CharField(
        max_length=200,  # Increased from 100 for longer company names
        help_text='Name of the company/vendor where purchase was made'
    )
    
    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow receipts without projects
        related_name='receipts',
        help_text='Project this expense is associated with'
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
@@ -91,53 +93,51 @@ class Receipt(models.Model):
    )
    
    # Receipt image
    receipt_image = models.ImageField(
        upload_to='receipts/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Upload an image of the receipt'
    )
    
    # Additional fields for better tracking
    notes = models.TextField(
        blank=True,
        help_text='Additional notes or comments about this receipt'
    )
    is_reimbursed = models.BooleanField(
        default=False,
        help_text='Whether this expense has been reimbursed'
    )
    reimbursement_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when reimbursement was processed'
    )
    
    # Timestamps provided by TimeStampedModel

    class Meta:
        ordering = ['-date_of_purchase', '-created_at']
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        indexes = [
            models.Index(fields=['date_of_purchase']),
            models.Index(fields=['project']),
            models.Index(fields=['worker']),
            models.Index(fields=['purchase_type']),
        ]

    def __str__(self):
        project_info = f"({self.project.job_num})" if self.project else "(No Project)"
        return f"{self.date_of_purchase} - {project_info} {self.company_name} - ${self.total_amount}"

    def get_absolute_url(self):
        """
        Returns the URL to access a detail record for this receipt.
        """
        return reverse('receipt-detail', args=[str(self.id)])

    @property
    def is_recent(self):
        """
