# hr/models.py - Universal HR Management Model

from django.db import models
from django.urls import reverse
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, Group, Permission)
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from decimal import Decimal
from datetime import date, timedelta
import uuid

# Import from your modernized apps
from client.models import Address, Contact, TimeStampedModel, UUIDModel
from location.models import BusinessCategory, ConfigurableChoice, get_dynamic_choices
from company.models import Company, Office, Department

class JobPosition(TimeStampedModel):
    """Job positions/roles within the company"""
    
    # Basic position information
    title = models.CharField(max_length=200, help_text='Position title')
    position_code = models.CharField(max_length=20, unique=True, help_text='Position code (MGR001, TECH001)')
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='positions',
        help_text='Department this position belongs to'
    )
    
    # Position hierarchy
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text='Position this role reports to'
    )
    
    # Job description
    description = models.TextField(blank=True, help_text='Job description')
    responsibilities = models.TextField(blank=True, help_text='Key responsibilities')
    requirements = models.TextField(blank=True, help_text='Required qualifications')
    
    # Compensation structure
    COMPENSATION_TYPES = [
        ('hourly', 'Hourly'),
        ('salary', 'Salary'),
        ('commission', 'Commission'),
        ('contract', 'Contract'),
    ]
    compensation_type = models.CharField(max_length=20, choices=COMPENSATION_TYPES, default='hourly')
    
    # Pay ranges
    min_hourly_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Minimum hourly rate'
    )
    max_hourly_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Maximum hourly rate'
    )
    min_annual_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Minimum annual salary'
    )
    max_annual_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Maximum annual salary'
    )
    
    # Employment type
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('seasonal', 'Seasonal'),
    ]
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    
    # Required credentials
    required_clearances = models.ManyToManyField('Clearance', blank=True, related_name='required_for_positions')
    required_certifications = models.ManyToManyField('Certification', blank=True, related_name='required_for_positions')
    
    # Job level
    JOB_LEVELS = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('executive', 'Executive'),
    ]
    job_level = models.CharField(max_length=20, choices=JOB_LEVELS, default='mid')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_billable = models.BooleanField(default=True, help_text='Can this position bill time to clients?')
    
    class Meta:
        app_label = 'hr'
        ordering = ['department', 'title']
        unique_together = ['department', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.department.name})"
    
    @property
    def current_employees(self):
        """Get current employees in this position"""
        return self.workers.filter(is_active=True, employment_status='active').count()

class Clearance(TimeStampedModel):
    """Security clearances and access levels"""
    
    name = models.CharField(max_length=200, unique=True, help_text='Clearance name')
    clearance_code = models.CharField(max_length=20, unique=True, help_text='Short code')
    description = models.TextField(blank=True, help_text='Clearance description')
    
    # Clearance details
    issuing_authority = models.CharField(max_length=200, blank=True, help_text='Who issues this clearance')
    clearance_level = models.CharField(max_length=50, blank=True, help_text='Clearance level (Secret, Top Secret, etc.)')
    
    # Validity
    requires_renewal = models.BooleanField(default=True)
    renewal_period_months = models.PositiveIntegerField(default=60, help_text='Renewal period in months')
    
    # Business category specific
    business_categories = models.ManyToManyField(
        BusinessCategory,
        blank=True,
        help_text='Which business types use this clearance'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'hr'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Certification(TimeStampedModel):
    """Professional certifications and training"""
    
    name = models.CharField(max_length=200, unique=True, help_text='Certification name')
    certification_code = models.CharField(max_length=20, unique=True, help_text='Short code')
    description = models.TextField(blank=True, help_text='Certification description')
    
    # Certification details
    issuing_organization = models.CharField(max_length=200, blank=True, help_text='Organization that issues certification')
    website_url = models.URLField(blank=True, help_text='Certification website')
    
    # Validity and renewal
    requires_renewal = models.BooleanField(default=True)
    renewal_period_months = models.PositiveIntegerField(default=24, help_text='Renewal period in months')
    continuing_education_required = models.BooleanField(default=False)
    
    # Cost and training
    typical_cost = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Typical certification cost'
    )
    training_hours_required = models.PositiveIntegerField(null=True, blank=True)
    
    # Business category specific
    business_categories = models.ManyToManyField(
        BusinessCategory,
        blank=True,
        help_text='Which business types use this certification'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'hr'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class WorkerManager(BaseUserManager):
    """Custom manager for Worker model"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a worker with the given email and password"""
        if not email:
            raise ValueError('Workers must have an email address')
        
        email = self.normalize_email(email)
        worker = self.model(email=email, **extra_fields)
        worker.set_password(password)
        worker.save(using=self._db)
        return worker
    
    def create_staffuser(self, email, password=None, **extra_fields):
        """Creates and saves a staff worker"""
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Creates and saves a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Worker(AbstractBaseUser, UUIDModel, TimeStampedModel):
    """Universal worker/employee model"""
    
    # Authentication
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True
    )
    
    # Personal information
    first_name = models.CharField(max_length=100, help_text='First name')
    last_name = models.CharField(max_length=100, help_text='Last name')
    middle_name = models.CharField(max_length=100, blank=True, help_text='Middle name')
    preferred_name = models.CharField(max_length=100, blank=True, help_text='Preferred name')
    
    # Contact information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Personal details
    date_of_birth = models.DateField(null=True, blank=True, help_text='Date of birth')
    
    gender = models.CharField(max_length=50, blank=True, default='')
    
    # Employment information
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='workers',
        help_text='Company'
    )
    
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Employee ID number'
    )
    
    position = models.ForeignKey(
        JobPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workers',
        help_text='Current position'
    )
    
    office = models.ForeignKey(
        Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workers',
        help_text='Primary office location'
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workers',
        help_text='Department'
    )
    
    # Reporting structure
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text='Direct manager'
    )
    
    # Employment details
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('resigned', 'Resigned'),
    ]
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='active'
    )
    
    date_of_hire = models.DateField(null=True, blank=True, help_text='Date of hire')
    date_of_termination = models.DateField(null=True, blank=True, help_text='Date of termination')
    
    # Compensation
    current_hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Current hourly rate'
    )
    current_annual_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Current annual salary'
    )
    
    # Professional information
    bio = models.TextField(max_length=500, blank=True, help_text='Professional biography')
    skills = models.JSONField(default=list, blank=True, help_text='Skills and competencies')
    
    # Documents
    profile_picture = models.ImageField(
        upload_to='uploads/workers/profiles/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Profile picture'
    )
    resume = models.FileField(
        upload_to='uploads/workers/resumes/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Resume/CV'
    )
    
    # Credentials
    clearances = models.ManyToManyField(
        Clearance,
        through='WorkerClearance',
        blank=True,
        related_name='workers'
    )
    certifications = models.ManyToManyField(
        Certification,
        through='WorkerCertification',
        blank=True,
        related_name='workers'
    )
    
    # System permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, help_text='Staff user (can access admin)')
    is_admin = models.BooleanField(default=False, help_text='Admin user')
    is_superuser = models.BooleanField(default=False, help_text='Superuser')

    # Group and permission relationships for compatibility with Django's auth system
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="worker_set",
        help_text="Groups this worker belongs to",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="worker_set",
        help_text="Specific permissions for this worker",
    )
    
    # Role-based permissions (customizable per business)
    roles = models.JSONField(default=list, blank=True, help_text='Business-specific roles')
    
    # Address information
    addresses = GenericRelation(Address)
    
    # Custom fields for business-specific data
    custom_fields = models.JSONField(default=dict, blank=True, help_text='Custom employee data')
    
    objects = WorkerManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        app_label = 'hr'
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['company', 'employment_status']),
            models.Index(fields=['department']),
            models.Index(fields=['manager']),
            models.Index(fields=['employee_id']),
        ]
    
    def __str__(self):
        return self.get_full_name()
    
    def get_absolute_url(self):
        return reverse('worker-detail', args=[str(self.id)])
    
    def get_full_name(self):
        """Return the full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def get_short_name(self):
        """Return the short name"""
        return self.preferred_name or self.first_name or self.email
    
    def get_display_name(self):
        """Return display name with preferred name if available"""
        if self.preferred_name:
            return f"{self.preferred_name} {self.last_name}"
        return self.get_full_name()
    
    # Permission methods (required by Django)
    def has_perm(self, perm, obj=None):
        """Does the worker have a specific permission?"""
        return self.is_admin
    
    def has_module_perms(self, app_label):
        """Does the worker have permissions to view the app?"""
        return self.is_staff
    
    # Employee information properties
    @property
    def age(self):
        """Calculate employee age"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def years_of_service(self):
        """Calculate years of service"""
        if self.date_of_hire:
            end_date = self.date_of_termination or date.today()
            return (end_date - self.date_of_hire).days / 365.25
        return 0
    
    @property
    def is_eligible_for_benefits(self):
        """Check if eligible for benefits (example logic)"""
        return self.employment_status == 'active' and self.years_of_service >= 0.25  # 3 months
    
    @property
    def primary_address(self):
        """Get the primary address"""
        return self.addresses.filter(is_primary=True, is_active=True).first()
    
    @property
    def current_clearances(self):
        """Get current active clearances"""
        return self.workerclearance_set.filter(
            is_active=True,
            expiration_date__gte=date.today()
        )
    
    @property
    def current_certifications(self):
        """Get current active certifications"""
        return self.workercertification_set.filter(
            is_active=True,
            expiration_date__gte=date.today()
        )
    
    @property
    def expiring_credentials(self):
        """Get credentials expiring within 60 days"""
        expiring_date = date.today() + timedelta(days=60)
        
        expiring_clearances = self.workerclearance_set.filter(
            is_active=True,
            expiration_date__lte=expiring_date,
            expiration_date__gte=date.today()
        )
        
        expiring_certs = self.workercertification_set.filter(
            is_active=True,
            expiration_date__lte=expiring_date,
            expiration_date__gte=date.today()
        )
        
        return {
            'clearances': expiring_clearances,
            'certifications': expiring_certs
        }

class WorkerClearance(TimeStampedModel):
    """Junction table for worker clearances with dates"""
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    clearance = models.ForeignKey(Clearance, on_delete=models.CASCADE)
    
    # Clearance details
    clearance_number = models.CharField(max_length=100, blank=True, help_text='Clearance ID/Number')
    granted_date = models.DateField(help_text='Date clearance was granted')
    expiration_date = models.DateField(null=True, blank=True, help_text='Expiration date')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Additional details
    granting_authority = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        app_label = 'hr'
        unique_together = ['worker', 'clearance']
        ordering = ['-granted_date']
    
    def __str__(self):
        return f"{self.worker.get_full_name()} - {self.clearance.name}"
    
    @property
    def is_expired(self):
        """Check if clearance is expired"""
        return self.expiration_date and self.expiration_date < date.today()
    
    @property
    def days_until_expiration(self):
        """Days until expiration"""
        if self.expiration_date:
            return (self.expiration_date - date.today()).days
        return None

class WorkerCertification(TimeStampedModel):
    """Junction table for worker certifications with dates"""
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    
    # Certification details
    certification_number = models.CharField(max_length=100, blank=True, help_text='Certification ID/Number')
    earned_date = models.DateField(help_text='Date certification was earned')
    expiration_date = models.DateField(null=True, blank=True, help_text='Expiration date')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Training details
    training_provider = models.CharField(max_length=200, blank=True)
    training_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    continuing_education_hours = models.PositiveIntegerField(default=0)
    
    # Documents
    certificate_file = models.FileField(
        upload_to='uploads/workers/certifications/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Certificate document'
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        app_label = 'hr'
        unique_together = ['worker', 'certification']
        ordering = ['-earned_date']
    
    def __str__(self):
        return f"{self.worker.get_full_name()} - {self.certification.name}"
    
    @property
    def is_expired(self):
        """Check if certification is expired"""
        return self.expiration_date and self.expiration_date < date.today()
    
    @property
    def days_until_expiration(self):
        """Days until expiration"""
        if self.expiration_date:
            return (self.expiration_date - date.today()).days
        return None

class TimeOffRequest(TimeStampedModel):
    """Time off and leave requests"""
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='time_off_requests')
    
    # Request details
    start_date = models.DateField(help_text='Start date of time off')
    end_date = models.DateField(help_text='End date of time off')
    
    TIME_OFF_TYPES = [
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Day'),
        ('bereavement', 'Bereavement'),
        ('jury_duty', 'Jury Duty'),
        ('military', 'Military Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
    ]
    time_off_type = models.CharField(max_length=20, choices=TIME_OFF_TYPES, default='vacation')
    
    is_paid = models.BooleanField(default=True, help_text='Is this paid time off?')
    reason = models.TextField(blank=True, help_text='Reason for time off')
    
    # Approval workflow
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('cancelled', 'Cancelled'),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )
    
    approved_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_off_requests'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    manager_notes = models.TextField(blank=True, help_text='Manager comments')
    
    class Meta:
        app_label = 'hr'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['worker', 'approval_status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.worker.get_full_name()} - {self.time_off_type} ({self.start_date})"
    
    @property
    def duration_days(self):
        """Calculate duration in days"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def is_future_request(self):
        """Check if request is for future dates"""
        return self.start_date > date.today()

class PerformanceReview(TimeStampedModel):
    """Employee performance reviews"""
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_reviews'
    )
    
    # Review period
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    review_date = models.DateField(default=date.today)
    
    REVIEW_TYPES = [
        ('annual', 'Annual Review'),
        ('probationary', 'Probationary Review'),
        ('mid_year', 'Mid-Year Review'),
        ('project', 'Project Review'),
        ('disciplinary', 'Disciplinary Review'),
    ]
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES, default='annual')
    
    # Ratings (1-5 scale)
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Overall performance rating (1-5)'
    )
    
    # Individual rating categories
    quality_of_work = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    productivity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    communication = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    teamwork = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    leadership = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Review content
    accomplishments = models.TextField(blank=True, help_text='Key accomplishments')
    areas_for_improvement = models.TextField(blank=True, help_text='Areas needing improvement')
    goals_for_next_period = models.TextField(blank=True, help_text='Goals for next review period')
    
    # Additional feedback
    manager_comments = models.TextField(blank=True, help_text='Manager comments')
    employee_comments = models.TextField(blank=True, help_text='Employee self-assessment')
    
    # Follow-up
    next_review_date = models.DateField(null=True, blank=True)
    
    class Meta:
        app_label = 'hr'
        ordering = ['-review_date']
        indexes = [
            models.Index(fields=['worker', 'review_date']),
            models.Index(fields=['review_type']),
        ]
    
    def __str__(self):
        return f"{self.worker.get_full_name()} - {self.review_type} ({self.review_date})"

# Default data creation functions
def create_default_hr_data():
    """Create default HR data for different business types"""
    
    # Create default clearances
    default_clearances = [
        ('BASIC_ACCESS', 'Basic Facility Access', 'General facility access'),
        ('CONFIDENTIAL', 'Confidential', 'Confidential clearance'),
        ('SECRET', 'Secret', 'Secret security clearance'),
        ('TOP_SECRET', 'Top Secret', 'Top secret security clearance'),
    ]
    
    for code, name, desc in default_clearances:
        Clearance.objects.get_or_create(
            clearance_code=code,
            defaults={'name': name, 'description': desc}
        )
    
    # Create default certifications
    default_certifications = [
        ('OSHA_10', 'OSHA 10-Hour', 'OSHA 10-hour safety training'),
        ('OSHA_30', 'OSHA 30-Hour', 'OSHA 30-hour safety training'),
        ('CPR_AED', 'CPR/AED', 'CPR and AED certification'),
        ('FIRST_AID', 'First Aid', 'Basic first aid certification'),
    ]
    
    for code, name, desc in default_certifications:
        Certification.objects.get_or_create(
            certification_code=code,
            defaults={'name': name, 'description': desc}
        )
    
    print("Default HR data created successfully!")
