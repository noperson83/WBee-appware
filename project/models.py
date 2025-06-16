# project/models.py - Modernized Project Model

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from decimal import Decimal
import uuid
from datetime import date

# Import from your modernized apps
from client.models import TimeStampedModel, UUIDModel
from location.models import Location, BusinessCategory, ConfigurableChoice, get_dynamic_choices
from hr.models import Worker
#from todo.models import Task
from material.models import Product

class ProjectTemplate(TimeStampedModel):
    """Templates for common project types per business category"""
    business_category = models.ForeignKey(
        BusinessCategory, 
        on_delete=models.CASCADE, 
        related_name='project_templates'
    )
    
    name = models.CharField(max_length=200, help_text='Template name')
    description = models.TextField(blank=True, help_text='Template description')
    
    # Default values for new projects
    estimated_duration_days = models.PositiveIntegerField(null=True, blank=True)
    default_markup = models.DecimalField(max_digits=5, decimal_places=2, default=1.15)
    default_burden = models.DecimalField(max_digits=5, decimal_places=2, default=1.65)
    
    # Template checklist/tasks
    template_tasks = models.JSONField(default=list, blank=True, help_text='Default tasks for this project type')
    required_materials = models.JSONField(default=list, blank=True, help_text='Common materials needed')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['business_category', 'name']
        unique_together = ['business_category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.business_category.name})"

class Project(UUIDModel, TimeStampedModel):
    """Modernized project model - works for any business type"""
    
    # Core identification
    job_number = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        help_text='Unique project identifier (can include letters)'
    )
    revision = models.CharField(
        max_length=50, 
        blank=True, 
        help_text='Project revision/version'
    )
    
    # Relationships
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE, 
        related_name='projects',
        help_text='Location where this project takes place'
    )
    
    template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Template used to create this project'
    )
    
    # Basic project information
    name = models.CharField(max_length=200, help_text='Project name')
    description = models.TextField(max_length=4000, blank=True, help_text='Detailed project description')
    scope_overview = models.TextField(max_length=2000, blank=True, help_text='High-level scope summary')
    
    # Visual documentation
    featured_image = models.ImageField(
        upload_to='uploads/project/images/%Y/%m/%d/', 
        null=True, 
        blank=True, 
        help_text='Main project image'
    )
    
    # Project contacts and team
    site_contact = models.TextField(max_length=500, blank=True, help_text='On-site contact information')
    
    # Team assignments (updated for flexibility)
    project_manager = models.ForeignKey(
        Worker, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_projects', 
        help_text='Project manager'
    )
    estimator = models.ForeignKey(
        Worker, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='estimated_projects', 
        help_text='Who estimated this project'
    )
    supervisor = models.ForeignKey(
        Worker, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='supervised_projects', 
        help_text='Field supervisor/foreman'
    )
    
    # Team members (many-to-many relationships)
    team_leads = models.ManyToManyField(
        Worker, 
        blank=True, 
        related_name='led_projects', 
        help_text='Team leads for this project'
    )
    team_members = models.ManyToManyField(
        Worker, 
        related_name='assigned_projects', 
        blank=True, 
        help_text='Team members assigned to this project'
    )
    
    # Timeline
    date_requested = models.DateField(null=True, blank=True, help_text='Date project was requested')
    start_date = models.DateField(null=True, blank=True, help_text='Planned start date')
    due_date = models.DateField(null=True, blank=True, help_text='Due date')
    completed_date = models.DateField(null=True, blank=True, help_text='Actual completion date')
    
    # Financial information
    estimated_cost = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated project cost'
    )
    contract_value = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Contract value'
    )
    
    # Pricing factors
    markup_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.15,
        validators=[MinValueValidator(Decimal('1.00')), MaxValueValidator(Decimal('5.00'))],
        help_text='Material markup (1.15 = 15% markup)'
    )
    burden_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.65,
        validators=[MinValueValidator(Decimal('1.00')), MaxValueValidator(Decimal('3.00'))],
        help_text='Labor burden percentage'
    )
    license_markup = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.15,
        validators=[MinValueValidator(Decimal('1.00')), MaxValueValidator(Decimal('3.00'))],
        help_text='Software/license markup'
    )
    
    # Payment tracking
    invoiced_amount = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        default=0,
        help_text='Amount invoiced to date'
    )
    paid_amount = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        default=0,
        help_text='Amount paid to date'
    )
    paid_date = models.DateField(null=True, blank=True, help_text='Date final payment received')
    
    # Dynamic status (configurable per business type)
    status = models.CharField(
        max_length=50, 
        default='prospect',
        db_index=True,
        help_text='Project status (configurable per business type)'
    )
    
    # Tax and business classification
    tax_status = models.CharField(
        max_length=50,
        default='taxable',
        help_text='Tax classification (configurable)'
    )
    
    division = models.CharField(
        max_length=50,
        blank=True,
        help_text='Business division/department (configurable)'
    )
    
    project_type = models.CharField(
        max_length=50,
        default='commercial',
        help_text='Project type classification (configurable)'
    )
    
    # Progress tracking
    percent_complete = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Completion percentage (0-100)'
    )
    
    # Quality and client satisfaction
    client_satisfaction_rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Client satisfaction (1-5 stars)'
    )
    
    # Risk and priority
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('normal', 'Normal Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Custom fields for business-specific data
    custom_fields = models.JSONField(default=dict, blank=True, help_text='Custom project data')
    
    # Internal notes (not visible to client)
    internal_notes = models.TextField(blank=True, help_text='Internal project notes')
    
    # Disclaimers and terms
    pricing_disclaimer = models.TextField(
        max_length=2000, 
        blank=True, 
        help_text='Pricing terms and disclaimers'
    )
    
    class Meta:
        ordering = ['-job_number']
        indexes = [
            models.Index(fields=['location', 'status']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['project_manager', 'status']),
            models.Index(fields=['job_number']),
            models.Index(fields=['start_date', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.job_number} - {self.name} ({self.location.name})"
    
    def get_absolute_url(self):
        return reverse('project-detail', args=[str(self.job_number)])
    
    # Business-specific terminology
    @property
    def business_category(self):
        """Get business category from location"""
        return self.location.business_category if self.location else None
    
    @property
    def project_term(self):
        """Get the business-specific term for this project"""
        if self.business_category:
            return self.business_category.project_term_singular
        return "Project"
    
    @property
    def project_term_plural(self):
        """Get the business-specific plural term"""
        if self.business_category:
            return self.business_category.project_term
        return "Projects"
    
    # Dynamic choice methods
    def get_available_statuses(self):
        """Get available statuses for this project's business category"""
        return get_dynamic_choices('project_status', self.business_category)
    
    def get_available_tax_statuses(self):
        """Get available tax statuses for this business category"""
        return get_dynamic_choices('tax_status', self.business_category)
    
    def get_available_divisions(self):
        """Get available divisions for this business category"""
        return get_dynamic_choices('division', self.business_category)
    
    def get_available_project_types(self):
        """Get available project types for this business category"""
        return get_dynamic_choices('project_type', self.business_category)
    
    # Financial calculations
    @property
    def profit_margin(self):
        """Calculate profit margin"""
        if self.contract_value and self.estimated_cost and self.estimated_cost > 0:
            return ((self.contract_value - self.estimated_cost) / self.contract_value) * 100
        return 0
    
    @property
    def outstanding_balance(self):
        """Calculate outstanding balance"""
        return (self.invoiced_amount or 0) - (self.paid_amount or 0)
    
    @property
    def revenue_to_date(self):
        """Calculate revenue earned based on completion percentage"""
        if self.contract_value and self.percent_complete:
            return (self.contract_value * self.percent_complete) / 100
        return 0
    
    @property
    def is_profitable(self):
        """Check if project is profitable"""
        return self.profit_margin > 0
    
    @property
    def is_overdue(self):
        """Check if project is overdue"""
        if self.due_date and not self.completed_date:
            return date.today() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date and not self.completed_date:
            return (self.due_date - date.today()).days
        return None
    
    @property
    def project_duration(self):
        """Calculate actual project duration"""
        if self.start_date and self.completed_date:
            return (self.completed_date - self.start_date).days
        return None
    
    # Task and material relationships
    @property
    def total_tasks(self):
        """Get total number of tasks"""
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        """Get number of completed tasks"""
        return self.tasks.filter(completed=True).count()
    
    @property
    def task_completion_percentage(self):
        """Calculate task completion percentage"""
        total = self.total_tasks
        if total > 0:
            return (self.completed_tasks / total) * 100
        return 0

    # Unified material access
    @property
    def device_items(self):
        return self.material_items.filter(material_type='device')

    @property
    def hardware_items(self):
        return self.material_items.filter(material_type='hardware')

    @property
    def software_items(self):
        return self.material_items.filter(material_type='software')

    @property
    def license_items(self):
        return self.material_items.filter(material_type='license')

    @property
    def travel_items(self):
        return self.material_items.filter(material_type='travel')

    # Material cost calculations
    def calculate_material_costs(self):
        """Calculate total material costs"""
        device_cost = sum(item.total for item in self.device_items)
        hardware_cost = sum(item.total for item in self.hardware_items)
        software_cost = sum(item.total for item in self.software_items)
        license_cost = sum(item.total for item in self.license_items)
        travel_cost = sum(item.total for item in self.travel_items)

        return {
            'device_cost': device_cost,
            'hardware_cost': hardware_cost,
            'software_cost': software_cost,
            'license_cost': license_cost,
            'travel_cost': travel_cost,
            'total_cost': device_cost + hardware_cost + software_cost + license_cost + travel_cost
        }
    
    # Project status management
    def mark_complete(self):
        """Mark project as complete"""
        self.completed_date = date.today()
        self.percent_complete = 100
        self.status = 'complete'
        self.save()
    
    def calculate_estimated_completion(self):
        """Estimate completion date based on progress"""
        if self.start_date and self.percent_complete > 0:
            days_elapsed = (date.today() - self.start_date).days
            if self.percent_complete > 0:
                estimated_total_days = (days_elapsed / self.percent_complete) * 100
                return self.start_date + timedelta(days=estimated_total_days)
        return None

# Scope of Work - Enhanced
class ScopeOfWork(TimeStampedModel):
    """Enhanced scope of work items"""
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='scope_items',
        help_text='Project this scope belongs to'
    )
    
    area = models.CharField(max_length=200, help_text='Area or location within the project')
    system_type = models.CharField(max_length=200, help_text='Type of system or work')
    description = models.TextField(blank=True, help_text='Detailed scope description')
    
    # Ordering and organization
    priority = models.PositiveIntegerField(default=100, help_text='Display order priority')
    phase = models.CharField(max_length=100, blank=True, help_text='Project phase (Phase 1, Phase 2, etc.)')
    
    # Progress tracking
    percent_complete = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    
    # Financial tracking per scope item
    estimated_cost = models.DecimalField(
        max_digits=18, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    actual_cost = models.DecimalField(
        max_digits=18, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Dependencies
    depends_on = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        help_text='Other scope items this depends on'
    )
    
    class Meta:
        ordering = ['priority', 'area']
        indexes = [
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['percent_complete']),
        ]
    
    def __str__(self):
        return f"{self.area} - {self.system_type}"
    
    @property
    def is_complete(self):
        return self.percent_complete >= 100
    
    @property
    def cost_variance(self):
        """Calculate cost variance"""
        if self.estimated_cost and self.actual_cost:
            return self.actual_cost - self.estimated_cost
        return None

# Enhanced material models (keeping your existing structure but with improvements)
class ProjectMaterial(TimeStampedModel):
    """Universal material item linked to a project."""

    MATERIAL_TYPES = [
        ('device', 'Device'),
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('license', 'License'),
        ('travel', 'Travel'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='material_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey("todo.Task", on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    scope_item = models.ForeignKey(ScopeOfWork, on_delete=models.SET_NULL, null=True, blank=True)

    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='device')

    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    delivered_date = models.DateField(null=True, blank=True)
    installed_date = models.DateField(null=True, blank=True)
    tested_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, default='quoted')
    installation_location = models.CharField(max_length=200, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)

    @property
    def total(self):
        return self.quantity * self.unit_cost

    class Meta:
        ordering = ['project', 'material_type']
        indexes = [
            models.Index(fields=['project', 'material_type']),
            models.Index(fields=['status']),
            models.Index(fields=['delivered_date']),
        ]

# Project change tracking

# Project change tracking
class ProjectChange(TimeStampedModel):
    """Track changes to projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='changes')
    change_type = models.CharField(max_length=50)  # scope_change, budget_change, schedule_change
    description = models.TextField()
    cost_impact = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    schedule_impact_days = models.IntegerField(default=0)
    
    requested_by = models.CharField(max_length=100, blank=True)
    approved_by = models.CharField(max_length=100, blank=True)
    approved_date = models.DateField(null=True, blank=True)
    
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']

# Project milestones
class ProjectMilestone(TimeStampedModel):
    """Track project milestones"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    target_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    
    is_critical = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['target_date']