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
        null=True,
        related_name='receipts',
        help_text='Employee who made the purchase'
    )
    purchase_type = models.ForeignKey(
        PurchaseType,
        on_delete=models.PROTECT,  # Prevent deletion of types in use
        related_name='receipts',
        help_text='Type of purchase made'
    )
    
    # Purchase details
    description = models.TextField(
        max_length=2000,  # Increased for more detailed descriptions
        blank=True,
        help_text='Detailed description of the purchase'
    )
    total_amount = models.DecimalField(
        max_digits=10,  # Reduced from 18 for more reasonable amounts
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Total amount of the purchase'
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
        Returns True if the receipt is from the last 30 days.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        return self.date_of_purchase >= (timezone.now().date() - timedelta(days=30))

    def clean(self):
        """
        Custom validation for the model.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        # Ensure reimbursement date is not before purchase date
        if self.reimbursement_date and self.reimbursement_date < self.date_of_purchase:
            raise ValidationError({
                'reimbursement_date': 'Reimbursement date cannot be before purchase date.'
            })
        
        # Ensure purchase date is not in the future
        if self.date_of_purchase > timezone.now().date():
            raise ValidationError({
                'date_of_purchase': 'Purchase date cannot be in the future.'
            })

    def save(self, *args, **kwargs):
        """
        Override save to perform custom validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)