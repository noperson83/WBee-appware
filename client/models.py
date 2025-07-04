# client/models.py - Modernized Client Model with Financial Schema

from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import uuid

# Abstract base models for consistency
class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class UUIDModel(models.Model):
    """Abstract model with UUID primary key"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True

# Address system (reusable across Client, Jobsite, etc.)
class Address(TimeStampedModel):
    """Flexible address model for any entity"""
    ADDRESS_TYPES = [
        ('billing', 'Billing Address'),
        ('shipping', 'Shipping Address'),
        ('site', 'Site Address'),
        ('mailing', 'Mailing Address'),
    ]
    
    label = models.CharField(max_length=50, choices=ADDRESS_TYPES)
    attention_line = models.CharField(max_length=100, blank=True, help_text='Attn: John Doe')
    line1 = models.CharField(max_length=200, help_text='Street address')
    line2 = models.CharField(max_length=200, blank=True, help_text='Apt, Suite, etc.')
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, help_text='State or Province')
    postal_code = models.CharField(max_length=20, help_text='ZIP or Postal Code')
    country = models.CharField(max_length=2, default='US', help_text='Country Code')
    
    # GPS coordinates for mapping
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Generic foreign key to attach to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-is_primary', 'label']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['postal_code']),
        ]
    
    def __str__(self):
        return f"{self.label}: {self.line1}, {self.city}, {self.state_province}"

# Contact system (also reusable)
class Contact(TimeStampedModel):
    """Flexible contact model"""
    CONTACT_TYPES = [
        ('primary', 'Primary Contact'),
        ('billing', 'Billing Contact'),
        ('technical', 'Technical Contact'),
        ('emergency', 'Emergency Contact'),
    ]
    
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    
    # Phone with validation
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\s().-]{7,20}$',
        message="Enter a valid phone number."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    mobile = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text="Mobile phone number",
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department or team",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the contact",
    )
    email = models.EmailField(blank=True)
    
    # Generic foreign key
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # Use CharField so contacts can reference models with UUID primary keys
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-is_primary', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.contact_type})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# Modern Client model
class Client(UUIDModel, TimeStampedModel):
    """Modernized client model with financial tracking"""
    # Basic company info
    company_name = models.CharField(max_length=200, db_index=True, help_text='Company name')
    company_url = models.URLField(blank=True, help_text='Company website')
    logo = models.ImageField(
        upload_to='uploads/client/logos/%Y/%m/%d/', 
        null=True, 
        blank=True, 
        help_text='Company logo'
    )
    
    # Business details
    BUSINESS_TYPES = [
        ('corporation', 'Corporation'),
        ('llc', 'LLC'),
        ('partnership', 'Partnership'),
        ('sole_prop', 'Sole Proprietorship'),
        ('non_profit', 'Non-Profit'),
        ('government', 'Government'),
    ]
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES, blank=True)
    tax_id = models.CharField(max_length=20, blank=True, help_text='EIN or Tax ID')
    
    # Client status and relationship
    CLIENT_STATUS = [
        ('prospect', 'Prospect'),
        ('active', 'Active Client'),
        ('inactive', 'Inactive'),
        ('former', 'Former Client'),
    ]
    status = models.CharField(max_length=20, choices=CLIENT_STATUS, default='prospect')
    
    # Important dates
    date_of_contact = models.DateField(null=True, blank=True, help_text='First contact date')
    date_of_contract = models.DateField(null=True, blank=True, help_text='First contract date')
    
    # Financial summary (calculated fields)
    ytd_revenue = models.DecimalField(
        max_digits=18, decimal_places=2, 
        null=True, blank=True, 
        help_text='Year to date revenue'
    )
    total_revenue = models.DecimalField(
        max_digits=18, decimal_places=2, 
        null=True, blank=True, 
        help_text='Total lifetime revenue'
    )
    
    # Payment terms and preferences
    PAYMENT_TERMS = [
        ('net_15', 'Net 15'),
        ('net_30', 'Net 30'),
        ('net_45', 'Net 45'),
        ('net_60', 'Net 60'),
        ('due_on_receipt', 'Due on Receipt'),
        ('custom', 'Custom Terms'),
    ]
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS, default='net_30')
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    # Client notes and summary
    summary = models.TextField(max_length=2000, blank=True, help_text='Client description and notes')
    
    # Custom fields for flexibility
    custom_fields = models.JSONField(default=dict, blank=True, help_text='Custom client data')
    
    # Related addresses and contacts via generic relations
    addresses = GenericRelation(Address)
    contacts = GenericRelation(Contact)
    
    class Meta:
        ordering = ["company_name"]
        verbose_name_plural = "Clients"
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['status']),
            models.Index(fields=['date_of_contact']),
        ]
    
    def __str__(self):
        return self.company_name

    def get_absolute_url(self):
        return reverse('client:detail', kwargs={'pk': self.pk})
    
    @property
    def primary_address(self):
        """Get the primary address"""
        return self.addresses.filter(is_primary=True, is_active=True).first()
    
    @property
    def primary_contact(self):
        """Get the primary contact"""
        return self.contacts.filter(is_primary=True, is_active=True).first()
    
    @property
    def billing_address(self):
        """Get billing address"""
        return self.addresses.filter(label='billing', is_active=True).first()


class ServiceLocation(UUIDModel, TimeStampedModel):
    """Simple service location tied to a client."""

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="service_locations",
    )
    name = models.CharField(max_length=200, help_text="Location name")
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="US")


    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.city}"

# Financial Schema Models
class FinancialPeriod(TimeStampedModel):
    """Define fiscal periods for reporting"""
    name = models.CharField(max_length=100, help_text='Q1 2025, FY 2025, etc.')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    PERIOD_TYPES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Period'),
    ]
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_current']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

class Revenue(TimeStampedModel):
    """Track revenue by client and period"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='revenues')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE)
    
    # Revenue breakdown
    contract_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    service_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    material_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    labor_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    # Additional revenue types
    change_order_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    warranty_revenue = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    # Calculated fields
    @property
    def total_revenue(self):
        return (self.contract_revenue + self.service_revenue + 
                self.material_revenue + self.labor_revenue + 
                self.change_order_revenue + self.warranty_revenue)
    
    class Meta:
        unique_together = ['client', 'period']
        indexes = [
            models.Index(fields=['client', 'period']),
            models.Index(fields=['period']),
        ]
    
    def __str__(self):
        return f"{self.client.company_name} - {self.period.name}: ${self.total_revenue:,.2f}"

class WIPReport(TimeStampedModel):
    """Work in Progress reporting model"""
    name = models.CharField(max_length=200, help_text='WIP Report Name')
    report_date = models.DateField(help_text='Report date')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE)
    
    # Cached calculations for performance
    total_backlog = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_wip = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_invoiced = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    # Status counts
    projects_prospecting = models.IntegerField(default=0)
    projects_quoted = models.IntegerField(default=0)
    projects_installing = models.IntegerField(default=0)
    projects_complete = models.IntegerField(default=0)
    projects_invoiced = models.IntegerField(default=0)
    projects_paid = models.IntegerField(default=0)
    
    # Report data as JSON for flexibility
    detailed_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['report_date']),
            models.Index(fields=['period']),
        ]
    
    def __str__(self):
        return f"WIP Report - {self.report_date}"

class ProjectFinancials(TimeStampedModel):
    """Detailed financial tracking per project"""
    # This would link to your existing Project model
    project_id = models.IntegerField(db_index=True, help_text='Link to existing Project')
    
    # Budget vs Actual tracking
    budgeted_labor_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_labor_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    budgeted_material_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_material_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    # Progress tracking
    percent_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    invoiced_to_date = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    collected_to_date = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    # Change orders
    change_order_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    @property
    def labor_variance(self):
        return self.actual_labor_hours - self.budgeted_labor_hours
    
    @property
    def material_variance(self):
        return self.actual_material_cost - self.budgeted_material_cost
    
    class Meta:
        indexes = [
            models.Index(fields=['project_id']),
            models.Index(fields=['percent_complete']),
        ]
    
    def __str__(self):
        return f"Financials for Project {self.project_id}"

# Management functions for automatic calculations
def update_client_revenue_totals():
    """Management command to recalculate client revenue totals"""
    from django.db.models import Sum
    from django.utils import timezone
    
    current_year = timezone.now().year
    
    for client in Client.objects.all():
        # Calculate YTD revenue
        ytd_revenue = Revenue.objects.filter(
            client=client,
            period__start_date__year=current_year
        ).aggregate(
            total=Sum('contract_revenue') + Sum('service_revenue') + 
                  Sum('material_revenue') + Sum('labor_revenue')
        )['total'] or 0
        
        # Calculate total revenue
        total_revenue = Revenue.objects.filter(
            client=client
        ).aggregate(
            total=Sum('contract_revenue') + Sum('service_revenue') + 
                  Sum('material_revenue') + Sum('labor_revenue')
        )['total'] or 0
        
        # Update client
        client.ytd_revenue = ytd_revenue
        client.total_revenue = total_revenue
        client.save(update_fields=['ytd_revenue', 'total_revenue'])

def generate_wip_report(report_date=None):
    """Generate WIP report data"""
    from django.utils import timezone
    from django.db.models import Sum, Count
    
    if not report_date:
        report_date = timezone.now().date()
    
    # This would integrate with your existing Project model
    # For now, showing the structure
    
    wip_data = {
        'backlog_by_status': {},
        'revenue_by_month': {},
        'top_clients': [],
        # Add more report sections as needed
    }
    
    return wip_data
