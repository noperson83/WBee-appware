# company/models.py - Modernized Company/Organization Model

from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericRelation
from decimal import Decimal
import uuid

# Import from your modernized client app
from client.models import Address, Contact, TimeStampedModel, UUIDModel
from location.models import BusinessCategory

class Company(UUIDModel, TimeStampedModel):
    """
    Model representing the main company/organization running Worker Bee
    (Not to be confused with Client which represents customers)
    """
    
    # Basic company information
    company_name = models.CharField(
        max_length=200, 
        db_index=True,
        help_text='Company/Organization name'
    )
    
    legal_name = models.CharField(
        max_length=200, 
        blank=True,
        help_text='Legal business name if different from display name'
    )
    
    company_url = models.URLField(blank=True, help_text='Company website')
    
    # Visual branding
    logo = models.ImageField(
        upload_to='uploads/company/logos/%Y/%m/%d/', 
        null=True, 
        blank=True, 
        help_text='Company logo'
    )
    
    button_image = models.ImageField(
        upload_to='uploads/company/buttons/%Y/%m/%d/', 
        null=True, 
        blank=True, 
        help_text='Button/icon image'
    )
    
    brand_colors = models.JSONField(
        default=dict, 
        blank=True,
        help_text='Brand colors (primary, secondary, etc.)'
    )
    
    # Business classification
    business_category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Primary business category'
    )

    business_config = models.ForeignKey(
        'business.BusinessConfiguration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Deployment business configuration'
    )
    
    BUSINESS_TYPES = [
        ('corporation', 'Corporation'),
        ('llc', 'LLC'),
        ('partnership', 'Partnership'),
        ('sole_prop', 'Sole Proprietorship'),
        ('non_profit', 'Non-Profit'),
        ('government', 'Government Agency'),
    ]
    business_type = models.CharField(
        max_length=20, 
        choices=BUSINESS_TYPES, 
        blank=True,
        help_text='Legal business structure'
    )
    
    # Tax and legal information
    tax_id = models.CharField(
        max_length=20, 
        blank=True, 
        help_text='EIN or Tax ID number'
    )
    
    business_license = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Business license number'
    )
    
    # Primary contact information
    primary_contact_name = models.CharField(
        max_length=200, 
        help_text='Primary contact person'
    )
    
    primary_contact_title = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Title of primary contact'
    )
    
    # Phone with validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    primary_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True,
        help_text='Primary phone number'
    )
    
    primary_email = models.EmailField(
        blank=True, 
        help_text='Primary business email'
    )
    
    # Company description and mission
    description = models.TextField(
        max_length=2000, 
        blank=True, 
        help_text='Company description and overview'
    )
    
    mission_statement = models.TextField(
        max_length=1000, 
        blank=True,
        help_text='Company mission statement'
    )
    
    # Important business dates
    founded_date = models.DateField(
        null=True, 
        blank=True, 
        help_text='Date company was founded'
    )
    
    # Financial tracking (company-wide)
    current_year_revenue = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Current year revenue'
    )
    
    previous_year_revenue = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Previous year revenue'
    )
    
    # Company settings and preferences
    TIMEZONE_CHOICES = [
        ('US/Eastern', 'Eastern Time'),
        ('US/Central', 'Central Time'),
        ('US/Mountain', 'Mountain Time'),
        ('US/Pacific', 'Pacific Time'),
        ('US/Alaska', 'Alaska Time'),
        ('US/Hawaii', 'Hawaii Time'),
    ]
    timezone = models.CharField(
        max_length=20,
        choices=TIMEZONE_CHOICES,
        default='US/Pacific',
        help_text='Company timezone'
    )
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
    ]
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text='Primary currency'
    )
    
    # System settings
    fiscal_year_start = models.PositiveIntegerField(
        default=1,
        help_text='Fiscal year start month (1=January, 4=April, etc.)'
    )
    
    default_payment_terms = models.CharField(
        max_length=50,
        default='Net 30',
        help_text='Default payment terms for invoices'
    )
    
    # Multi-location/subsidiary support
    is_multi_location = models.BooleanField(
        default=False,
        help_text='Does this company have multiple locations?'
    )
    
    parent_company = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subsidiaries',
        help_text='Parent company if this is a subsidiary'
    )

    # Collaboration
    primary_company = models.BooleanField(
        default=False,
        help_text='Main company in a collaborative deployment'
    )

    collaboration_permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text='Permissions for cross-company collaboration'
    )

    partner_companies = models.ManyToManyField(
        'self',
        through='CompanyPartnership',
        symmetrical=False,
        related_name='partners',
        blank=True,
        help_text='Partner companies in collaborative deployments'
    )
    
    # Custom fields for business-specific data
    custom_fields = models.JSONField(
        default=dict, 
        blank=True, 
        help_text='Custom company data'
    )
    
    # Related addresses and contacts via generic relations
    addresses = GenericRelation(Address)
    contacts = GenericRelation(Contact)
    
    # Status
    is_active = models.BooleanField(default=True, help_text='Is company active?')
    
    class Meta:
        ordering = ["company_name"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['business_category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.company_name
    
    def get_absolute_url(self):
        """Return the canonical URL for this company."""
        return reverse("company:detail", kwargs={"pk": self.pk})
    
    @property
    def primary_address(self):
        """Get the primary address"""
        return self.addresses.filter(is_primary=True, is_active=True).first()
    
    @property
    def headquarters_address(self):
        """Get headquarters address"""
        return self.addresses.filter(label='headquarters', is_active=True).first()
    
    @property
    def billing_address(self):
        """Get billing address"""
        return self.addresses.filter(label='billing', is_active=True).first()
    
    @property
    def total_locations(self):
        """Get total number of office locations"""
        return self.offices.filter(is_active=True).count()
    
    @property
    def total_departments(self):
        """Get total number of departments"""
        return self.departments.filter(is_active=True).count()
    
    @property
    def total_employees(self):
        """Get total number of employees across all offices"""
        try:
            from hr.models import Worker
            return Worker.objects.filter(office__company=self, is_active=True).count()
        except:
            return 0
    
    @property
    def revenue_growth(self):
        """Calculate year-over-year revenue growth"""
        if self.current_year_revenue and self.previous_year_revenue and self.previous_year_revenue > 0:
            return ((self.current_year_revenue - self.previous_year_revenue) / self.previous_year_revenue) * 100
        return 0
    
    @property
    def is_subsidiary(self):
        """Check if this is a subsidiary company"""
        return self.parent_company is not None
    
    @property
    def has_subsidiaries(self):
        """Check if this company has subsidiaries"""
        return self.subsidiaries.exists()

    @property
    def business_config_summary(self):
        """Get summary of business configuration"""
        if not self.business_config:
            return None
        return {
            'name': self.business_config.name,
            'deployment_type': self.business_config.get_deployment_type_display(),
            'billing_model': self.business_config.get_billing_model_display(),
            'collaboration_features': self.business_config.collaboration_features,
            'is_collaborative': self.business_config.is_collaborative,
        }

    def apply_business_template(self, template_slug: str) -> bool:
        """Apply a business template to this company"""
        from business.models import BusinessTemplate
        try:
            template = BusinessTemplate.objects.get(slug=template_slug, is_active=True)
            return template.apply_to_company(self)
        except BusinessTemplate.DoesNotExist:
            return False


class CompanyPartnership(TimeStampedModel):
    """Junction model representing partnerships between companies."""

    PARTNERSHIP_TYPES = [
        ('strategic', 'Strategic'),
        ('supplier', 'Supplier'),
        ('subcontractor', 'Subcontractor'),
        ('affiliate', 'Affiliate'),
    ]

    from_company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='partnerships_initiated'
    )
    to_company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='partnerships_received'
    )

    partnership_type = models.CharField(
        max_length=20,
        choices=PARTNERSHIP_TYPES,
        default='strategic'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['from_company', 'to_company']
        ordering = ['from_company', 'to_company']

    def __str__(self):
        return f"{self.from_company} → {self.to_company} ({self.partnership_type})"

class Office(UUIDModel, TimeStampedModel):
    """
    Model representing company offices/locations
    """
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        null=True, blank=True, 
        related_name='offices',
        help_text='Company this office belongs to'
    )
    
    # Basic office information
    office_name = models.CharField(
        max_length=200, 
        help_text='Office name (Tucson, Phoenix, Headquarters, etc.)'
    )
    
    office_code = models.CharField(
        max_length=10,
        blank=True,
        help_text='Short code for this office (TUC, PHX, HQ)'
    )
    
    OFFICE_TYPES = [
        ('headquarters', 'Headquarters'),
        ('branch', 'Branch Office'),
        ('warehouse', 'Warehouse'),
        ('retail', 'Retail Location'),
        ('field_office', 'Field Office'),
        ('remote', 'Remote Office'),
    ]
    office_type = models.CharField(
        max_length=20,
        choices=OFFICE_TYPES,
        default='branch'
    )
    
    # Office details
    description = models.TextField(
        max_length=1000, 
        blank=True,
        help_text='Office description and details'
    )
    
    # Capacity and logistics
    employee_capacity = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Maximum number of employees'
    )
    
    square_footage = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Office size in square feet'
    )
    
    # Operating information
    office_manager = models.CharField(
        max_length=200, 
        blank=True,
        help_text='Office manager name'
    )
    
    phone_number = models.CharField(
        max_length=17, 
        blank=True,
        help_text='Office phone number'
    )
    
    email = models.EmailField(
        blank=True,
        help_text='Office email address'
    )
    
    # Operating hours
    operating_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text='Operating hours by day of week'
    )
    
    # Related addresses via generic relations
    addresses = GenericRelation(Address)
    
    # Status and dates
    opened_date = models.DateField(
        null=True, 
        blank=True,
        help_text='Date office opened'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['company', 'office_name']
        unique_together = ['company', 'office_name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['office_type']),
        ]
    
    def __str__(self):
        return f"{self.office_name} ({self.company.company_name})"
    
    def get_absolute_url(self):
        return reverse('office-detail', args=[str(self.id)])
    
    @property
    def primary_address(self):
        """Get the primary address for this office"""
        return self.addresses.filter(is_primary=True, is_active=True).first()
    
    @property
    def employee_count(self):
        """Get current number of employees at this office"""
        try:
            from hr.models import Worker
            return Worker.objects.filter(office=self, is_active=True).count()
        except:
            return 0
    
    @property
    def utilization_rate(self):
        """Calculate office utilization rate"""
        if self.employee_capacity and self.employee_capacity > 0:
            return (self.employee_count / self.employee_capacity) * 100
        return 0

class Department(TimeStampedModel):
    """
    Model representing company departments
    """
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='departments',
        help_text='Company this department belongs to'
    )
    
    # Basic department information
    name = models.CharField(
        max_length=100, 
        help_text='Department name'
    )
    
    department_code = models.CharField(
        max_length=10,
        blank=True,
        help_text='Short code for department (SALES, IT, HR)'
    )
    
    description = models.TextField(
        max_length=1000, 
        blank=True,
        help_text='Department description and responsibilities'
    )
    
    # Department hierarchy
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_departments',
        help_text='Parent department if this is a sub-department'
    )
    
    # Department leadership
    department_head = models.CharField(
        max_length=200, 
        blank=True,
        help_text='Department head/manager name'
    )
    
    # Budget and financial
    annual_budget = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Annual department budget'
    )
    
    cost_center_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Cost center code for accounting'
    )
    
    # Office association
    primary_office = models.ForeignKey(
        Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_departments',
        help_text='Primary office for this department'
    )
    
    # Department settings
    is_billable = models.BooleanField(
        default=True,
        help_text='Can this department bill time to clients?'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['company', 'name']
        unique_together = ['company', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['parent_department']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.company.company_name})"
    
    def get_absolute_url(self):
        return reverse('department-detail', args=[str(self.id)])
    
    @property
    def employee_count(self):
        """Get number of employees in this department"""
        try:
            from hr.models import Worker
            return Worker.objects.filter(department=self, is_active=True).count()
        except:
            return 0
    
    @property
    def is_sub_department(self):
        """Check if this is a sub-department"""
        return self.parent_department is not None
    
    @property
    def has_sub_departments(self):
        """Check if this department has sub-departments"""
        return self.sub_departments.exists()
    
    @property
    def full_department_path(self):
        """Return the department hierarchy path without infinite recursion"""
        names = []
        current = self
        visited = set()
        while current is not None:
            if current.pk in visited:
                # Break on cycles to avoid infinite recursion
                break
            names.append(current.name)
            visited.add(current.pk)
            current = current.parent_department
        return " > ".join(reversed(names))

# Company settings model for system-wide configurations
class CompanySettings(TimeStampedModel):
    """
    System-wide settings and configurations
    """
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Invoice and billing settings
    invoice_prefix = models.CharField(
        max_length=10,
        default='INV',
        help_text='Prefix for invoice numbers'
    )
    
    next_invoice_number = models.PositiveIntegerField(
        default=1000,
        help_text='Next invoice number to use'
    )
    
    # Project numbering
    project_prefix = models.CharField(
        max_length=10,
        default='P',
        help_text='Prefix for project numbers'
    )
    
    next_project_number = models.PositiveIntegerField(
        default=1000,
        help_text='Next project number to use'
    )
    
    # Email settings
    smtp_server = models.CharField(max_length=200, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=200, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    
    # System preferences
    date_format = models.CharField(
        max_length=20,
        default='MM/DD/YYYY',
        help_text='Preferred date format'
    )
    
    # Notification settings
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Email and notification preferences'
    )
    
    # Integration settings
    integrations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Third-party integration settings'
    )
    
    class Meta:
        verbose_name = "Company Settings"
        verbose_name_plural = "Company Settings"

# Management functions
def get_active_company():
    """Get the active company (for single-tenant setups)"""
    return Company.objects.filter(is_active=True).first()

def setup_default_company_data(company):
    """Set up default departments and settings for a new company"""
    
    # Create default departments
    default_departments = [
        ('Administration', 'ADMIN'),
        ('Sales', 'SALES'),
        ('Operations', 'OPS'),
        ('Accounting', 'ACCT'),
    ]
    
    for dept_name, dept_code in default_departments:
        Department.objects.get_or_create(
            company=company,
            name=dept_name,
            defaults={'department_code': dept_code}
        )
    
    # Create company settings
    CompanySettings.objects.get_or_create(company=company)
