from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from decimal import Decimal
import uuid

# Import from your modernized client app
from client.models import Client, Address, Contact, TimeStampedModel, UUIDModel

# Dynamic configuration models for any business type
class BusinessCategory(TimeStampedModel):
    """Define different business categories (Construction, Entertainment, Investigation, etc.)"""
    name = models.CharField(max_length=100, help_text='Construction, Entertainment, Investigation, Consulting, etc.')
    description = models.TextField(blank=True, help_text='Description of this business category')
    icon = models.CharField(max_length=50, blank=True, help_text='Font Awesome icon class')
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    is_active = models.BooleanField(default=True)
    
    # Customizable terminology
    project_nickname = models.CharField(
        max_length=50, 
        default='Projects',
        help_text='What to call "Projects" in this business (Jobs, Deliveries, Cases, Events, etc.)'
    )
    project_nickname_singular = models.CharField(
        max_length=50,
        default='Project',
        help_text='Singular form (Job, Delivery, Case, Event, etc.)'
    )

    # New universal terminology fields
    client_nickname = models.CharField(
        max_length=50,
        default='Clients',
        help_text='Plural term for clients (Bars, Customers, etc.)'
    )
    client_nickname_singular = models.CharField(
        max_length=50,
        default='Client',
        help_text='Singular client term'
    )
    location_nickname = models.CharField(
        max_length=50,
        default='Locations',
        help_text='Plural term for locations (Venues, Sites, etc.)'
    )
    location_nickname_singular = models.CharField(
        max_length=50,
        default='Location',
        help_text='Singular location term'
    )
    material_nickname = models.CharField(
        max_length=50,
        default='Materials',
        help_text='Plural term for materials/inventory'
    )
    material_nickname_singular = models.CharField(
        max_length=50,
        default='Material',
        help_text='Singular material term'
    )
    material_type_nicknames = models.JSONField(
        default=dict,
        blank=True,
        help_text='Nicknames for material types (device, hardware, etc.)'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Business Categories"
    
    def __str__(self):
        return self.name
    
    @property 
    def project_term(self):
        """Get the project terminology for this business"""
        return self.project_nickname
    
    @property
    def project_term_singular(self):
        """Get the singular project terminology"""
        return self.project_nickname_singular

    @property
    def client_term(self):
        """Plural client terminology"""
        return self.client_nickname

    @property
    def client_term_singular(self):
        return self.client_nickname_singular

    @property
    def location_term(self):
        return self.location_nickname

    @property
    def location_term_singular(self):
        return self.location_nickname_singular

    @property
    def material_term(self):
        return self.material_nickname

    @property
    def material_term_singular(self):
        return self.material_nickname_singular

    def get_material_type_term(self, slug):
        return self.material_type_nicknames.get(slug, slug.title())

class ConfigurableChoice(TimeStampedModel):
    """Dynamic choices for any field across the system"""
    category = models.ForeignKey(BusinessCategory, on_delete=models.CASCADE, related_name='choices')
    
    CHOICE_TYPES = [
        # Location related
        ('location_type', 'Location Type'),
        ('location_status', 'Location Status'),
        ('access_requirement', 'Access Requirement'),
        ('work_hours', 'Work Hours'),
        
        # Document related
        ('document_type', 'Document Type'),
        ('note_type', 'Note Type'),
        ('priority_level', 'Priority Level'),
        
        # Project related (for future use)
        ('project_status', 'Project Status'),
        ('task_type', 'Task Type'),
        
        # Custom
        ('custom', 'Custom Field Choice'),
    ]
    
    choice_type = models.CharField(max_length=30, choices=CHOICE_TYPES)
    value = models.CharField(max_length=50, help_text='The actual value stored in database')
    display_name = models.CharField(max_length=100, help_text='What users see')
    description = models.TextField(blank=True, help_text='Description of this choice')
    
    # Ordering and visibility
    sort_order = models.PositiveIntegerField(default=100, help_text='Display order')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text='Default selection?')
    
    # Business-specific visibility
    applicable_to_all = models.BooleanField(default=True, help_text='Available to all business types?')
    
    class Meta:
        ordering = ['choice_type', 'sort_order', 'display_name']
        unique_together = ['category', 'choice_type', 'value']
        indexes = [
            models.Index(fields=['choice_type', 'is_active']),
            models.Index(fields=['category', 'choice_type']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.choice_type})"

# Helper function to get dynamic choices
def get_dynamic_choices(choice_type, category=None):
    """Get choices for a field type, optionally filtered by business category"""
    queryset = ConfigurableChoice.objects.filter(
        choice_type=choice_type,
        is_active=True
    )
    
    if category:
        queryset = queryset.filter(
            models.Q(category=category) | models.Q(applicable_to_all=True)
        )
    
    return [(choice.value, choice.display_name) for choice in queryset.order_by('sort_order', 'display_name')]

class LocationType(TimeStampedModel):
    """Define different types of locations - now business agnostic"""
    business_category = models.ForeignKey(BusinessCategory, on_delete=models.CASCADE, related_name='location_types')
    name = models.CharField(max_length=100, help_text='Office Building, Concert Venue, Crime Scene, Film Set, etc.')
    description = models.TextField(blank=True, help_text='Description of this location type')
    typical_systems = models.JSONField(default=list, blank=True, help_text='Common systems/equipment for this type')
    
    class Meta:
        ordering = ['business_category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.business_category.name})"

class Location(UUIDModel, TimeStampedModel):
    """Modernized location model - works for any business type"""
    
    # Relationship to client and business type
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name="locations", 
        help_text='Client who owns this location'
    )
    
    business_category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Type of business (Construction, Entertainment, Investigation, etc.)'
    )
    
    # Basic location information
    name = models.CharField(max_length=200, db_index=True, help_text='Location name')
    location_type = models.ForeignKey(
        LocationType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Type of facility/location'
    )
    
    # Enhanced description
    description = models.TextField(max_length=2000, help_text='Detailed location description')
    scope_summary = models.TextField(max_length=1000, blank=True, help_text='High-level scope overview')
    
    # Visual documentation
    profile_image = models.ImageField(
        upload_to='uploads/location/profile/%Y/%m/%d/', 
        null=True, 
        blank=True, 
        help_text='Main location photo'
    )
    
    # Dynamic location types (configurable)
    location_category = models.CharField(
        max_length=50, 
        blank=True,
        help_text='Urban, Rural, Indoor, Outdoor, etc. (configurable)'
    )
    
    # GPS coordinates with validation
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text='Longitude coordinate'
    )
    
    # Maps integration
    google_maps_url = models.URLField(
        blank=True, 
        help_text='Google Maps link for directions'
    )
    google_plus_code = models.CharField(
        max_length=20, 
        blank=True,
        help_text='Google Plus Code (e.g., 9G8F+5W)'
    )
    
    # Dynamic status (configurable per business type)
    status = models.CharField(
        max_length=50, 
        default='prospect',
        help_text='Configurable status based on business type'
    )
    
    # Important dates
    first_contact_date = models.DateField(null=True, blank=True, help_text='First contact date')
    site_survey_date = models.DateField(null=True, blank=True, help_text='Site survey/assessment date')
    contract_signed_date = models.DateField(null=True, blank=True, help_text='Contract/agreement date')
    project_start_date = models.DateField(null=True, blank=True, help_text='First project start')
    estimated_completion = models.DateField(null=True, blank=True, help_text='Estimated completion')
    
    # Facility details (flexible for any business)
    facility_size = models.PositiveIntegerField(null=True, blank=True, help_text='Size (sq ft, acres, seats, etc.)')
    facility_size_unit = models.CharField(max_length=20, default='sq_ft', help_text='Unit of measurement')
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text='People capacity if applicable')
    
    # Existing infrastructure/equipment
    existing_systems = models.JSONField(
        default=list, 
        blank=True,
        help_text='List of existing systems/equipment'
    )
    
    # Dynamic access requirements (configurable)
    access_requirements = models.CharField(
        max_length=50, 
        default='none',
        help_text='Configurable access requirements'
    )
    
    # Dynamic work hours (configurable)
    work_hours = models.CharField(
        max_length=50, 
        default='standard',
        help_text='Configurable work hours/availability'
    )
    
    # Special considerations
    special_requirements = models.TextField(
        blank=True,
        help_text='Special safety, access, or work requirements'
    )
    
    # Emergency contacts and procedures
    emergency_contact_info = models.JSONField(
        default=dict,
        blank=True,
        help_text='Emergency contact information'
    )
    
    # Financial summary (calculated from projects)
    total_contract_value = models.DecimalField(
        max_digits=18, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Total value of all contracts at this location'
    )
    
    # Logistics (flexible for different business types)
    parking_available = models.BooleanField(default=True, help_text='Parking available for team')
    loading_access = models.BooleanField(default=False, help_text='Loading/equipment access')
    storage_available = models.BooleanField(default=False, help_text='On-site storage available')
    
    # Custom fields for ultimate flexibility
    custom_fields = models.JSONField(default=dict, blank=True, help_text='Custom location data')
    
    # Related addresses and contacts via generic relations
    addresses = GenericRelation(Address)
    contacts = GenericRelation(Contact)
    
    class Meta:
        ordering = ['-contract_signed_date', 'name']
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['business_category', 'status']),
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['contract_signed_date']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.client.company_name})"
    
    def get_absolute_url(self):
        return reverse('location:location-detail', args=[str(self.id)])
    
    # Dynamic choice methods
    def get_available_statuses(self):
        """Get available statuses for this location's business category"""
        return get_dynamic_choices('location_status', self.business_category)
    
    def get_available_location_types(self):
        """Get available location types for this business category"""
        return get_dynamic_choices('location_type', self.business_category)
    
    def get_available_access_requirements(self):
        """Get available access requirements for this business category"""
        return get_dynamic_choices('access_requirement', self.business_category)
    
    def get_available_work_hours(self):
        """Get available work hours for this business category"""
        return get_dynamic_choices('work_hours', self.business_category)
    
    @property
    def primary_address(self):
        """Get the primary address for this location"""
        return self.addresses.filter(is_primary=True, is_active=True).first()
    
    @property
    def site_contact(self):
        """Get the primary site contact"""
        return self.contacts.filter(contact_type='primary', is_active=True).first()
    
    @property
    def full_address_display(self):
        """Display the full address as a string"""
        address = self.primary_address
        if address:
            return f"{address.line1}, {address.city}, {address.state_province} {address.postal_code}"
        return "No address specified"
    
    @property
    def active_projects_count(self):
        """Count of active projects at this location"""
        try:
            return self.projects.exclude(status__in=['c', 'm', 'l']).count()
        except:
            return 0
    
    @property
    def total_projects_count(self):
        """Total count of all projects"""
        try:
            return self.projects.count()
        except:
            return 0
    
    @property
    def coordinates(self):
        """Return coordinates as a tuple"""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None
    
    @property
    def google_maps_embed_url(self):
        """Generate Google Maps embed URL"""
        if self.coordinates:
            lat, lng = self.coordinates
            return f"https://www.google.com/maps/embed/v1/place?key={settings.GOOGLE_MAPS_API_KEY}&q={lat},{lng}"
        return None
    
    @property
    def project_term(self):
        """Get the business-specific term for projects"""
        if self.business_category:
            return self.business_category.project_term
        return "Projects"
    
    @property
    def project_term_singular(self):
        """Get the business-specific singular term for projects"""
        if self.business_category:
            return self.business_category.project_term_singular
        return "Project"
    
    def calculate_total_contract_value(self):
        """Calculate total contract value from all projects"""
        try:
            from project.models import Project  # Avoid circular import
            total = Project.objects.filter(
                location=self
            ).aggregate(
                total=models.Sum('contract_value')
            )['total'] or Decimal('0.00')
            
            self.total_contract_value = total
            self.save(update_fields=['total_contract_value'])
            return total
        except ImportError:
            return Decimal('0.00')
    
    def get_project_status_summary(self):
        """Get summary of project statuses at this location"""
        try:
            from project.models import Project
            return Project.objects.filter(location=self).values('status').annotate(
                count=models.Count('status')
            )
        except ImportError:
            return []

class LocationDocument(TimeStampedModel):
    """Documents related to a location - configurable for any business type"""
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    
    # Dynamic document types (configurable)
    document_type = models.CharField(
        max_length=50,
        help_text='Configurable document type based on business category'
    )
    
    title = models.CharField(max_length=200, help_text='Document title')
    description = models.TextField(blank=True, help_text='Document description')
    
    file = models.FileField(
        upload_to='uploads/location/documents/%Y/%m/%d/',
        help_text='Upload document file'
    )
    
    # Version control
    version = models.CharField(max_length=20, default='1.0', help_text='Document version')
    is_current = models.BooleanField(default=True, help_text='Is this the current version?')
    
    # Access control
    is_public = models.BooleanField(default=False, help_text='Visible to client?')
    
    uploaded_by = models.CharField(max_length=100, blank=True, help_text='Who uploaded this')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location', 'document_type']),
            models.Index(fields=['is_current']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.location.name})"
    
    def get_available_document_types(self):
        """Get available document types for this location's business category"""
        return get_dynamic_choices('document_type', self.location.business_category)

class LocationNote(TimeStampedModel):
    """Notes and updates about a location - configurable for any business type"""
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE, 
        related_name='notes'
    )
    
    # Dynamic note types (configurable)
    note_type = models.CharField(
        max_length=50, 
        default='general',
        help_text='Configurable note type'
    )
    
    title = models.CharField(max_length=200, help_text='Note title')
    content = models.TextField(help_text='Note content')
    
    # Dynamic priority levels (configurable)
    priority = models.CharField(
        max_length=20, 
        default='normal',
        help_text='Configurable priority level'
    )
    
    is_client_visible = models.BooleanField(default=False, help_text='Show to client?')
    requires_followup = models.BooleanField(default=False, help_text='Needs follow-up?')
    followup_date = models.DateField(null=True, blank=True, help_text='Follow-up by date')
    
    created_by = models.CharField(max_length=100, blank=True, help_text='Who created this note')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location', 'note_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['requires_followup']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.location.name}"
    
    def get_available_note_types(self):
        """Get available note types for this location's business category"""
        return get_dynamic_choices('note_type', self.location.business_category)
    
    def get_available_priority_levels(self):
        """Get available priority levels for this location's business category"""
        return get_dynamic_choices('priority_level', self.location.business_category)

# Default data creation function
def create_default_business_categories():
    """Create default business categories and their choices"""
    
    # Business Categories
    construction = BusinessCategory.objects.get_or_create(
        name='Construction & AV',
        defaults={
            'description': 'Construction, electrical, AV installation, security systems',
            'icon': 'fas fa-hard-hat',
            'color': '#f39c12',
            'project_nickname': 'Installs',
            'project_nickname_singular': 'Install'
        }
    )[0]
    
    entertainment = BusinessCategory.objects.get_or_create(
        name='Entertainment',
        defaults={
            'description': 'Concerts, events, touring, venues, production',
            'icon': 'fas fa-music',
            'color': '#e91e63',
            'project_nickname': 'Shows',
            'project_nickname_singular': 'Show'
        }
    )[0]
    
    investigation = BusinessCategory.objects.get_or_create(
        name='Investigation',
        defaults={
            'description': 'Private investigation, security, surveillance',
            'icon': 'fas fa-search',
            'color': '#34495e',
            'project_nickname': 'Cases',
            'project_nickname_singular': 'Case'
        }
    )[0]
    
    consulting = BusinessCategory.objects.get_or_create(
        name='Consulting',
        defaults={
            'description': 'Business consulting, professional services',
            'icon': 'fas fa-briefcase',
            'color': '#3498db'
        }
    )[0]
    
    # Distribution & Logistics
    distribution = BusinessCategory.objects.get_or_create(
        name='Distribution & Logistics',
        defaults={
            'description': 'Liquid distribution, delivery, warehousing, supply chain',
            'icon': 'fas fa-truck',
            'color': '#27ae60',
            'project_nickname': 'Deliveries',
            'project_nickname_singular': 'Delivery'
        }
    )[0]
    
    # Food & Beverage
    food_beverage = BusinessCategory.objects.get_or_create(
        name='Food & Beverage',
        defaults={
            'description': 'Restaurants, catering, food service, beverage production',
            'icon': 'fas fa-utensils',
            'color': '#e67e22',
            'project_nickname': 'Events',
            'project_nickname_singular': 'Event'
        }
    )[0]
    
    # Healthcare Services
    healthcare = BusinessCategory.objects.get_or_create(
        name='Healthcare Services',
        defaults={
            'description': 'Home healthcare, medical equipment, patient care',
            'icon': 'fas fa-heartbeat',
            'color': '#e74c3c',
            'project_nickname': 'Visits',
            'project_nickname_singular': 'Visit'
        }
    )[0]
    
    # Create some default configurable choices
    default_statuses = [
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('complete', 'Complete'),
        ('inactive', 'Inactive'),
    ]
    
    for category in [construction, entertainment, investigation, consulting, distribution, food_beverage, healthcare]:
        for i, (value, display) in enumerate(default_statuses):
            ConfigurableChoice.objects.get_or_create(
                category=category,
                choice_type='location_status',
                value=value,
                defaults={
                    'display_name': display,
                    'sort_order': i * 10,
                    'applicable_to_all': True
                }
            )

# Management functions
def update_all_location_totals():
    """Update contract totals for all locations"""
    for location in Location.objects.all():
        location.calculate_total_contract_value()

def get_locations_needing_followup():
    """Get locations with notes requiring follow-up"""
    from django.utils import timezone
    return Location.objects.filter(
        notes__requires_followup=True,
        notes__followup_date__lte=timezone.now().date()
    ).distinct()
