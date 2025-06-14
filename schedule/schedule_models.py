# schedule/models.py - Modernized Calendar and Event Models

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import timedelta, time
from decimal import Decimal
from django.core.validators import MinValueValidator
from schedule.models.rules import Rule
from hr.models import Worker
from project.models import Project
from material.models import Supplier

# Shared abstract base models
from client.models import TimeStampedModel

# Import your existing CalendarManager and EventRelationManager
# (keeping the existing manager code as it's well-designed)

class CalendarManager(models.Manager):
    def get_calendar_for_object(self, obj, distinction=''):
        """Get single calendar for an object"""
        calendar_list = self.get_calendars_for_object(obj, distinction)
        if len(calendar_list) == 0:
            raise Calendar.DoesNotExist("Calendar does not exist.")
        elif len(calendar_list) > 1:
            raise AssertionError("More than one calendars were found.")
        else:
            return calendar_list[0]

    def get_or_create_calendar_for_object(self, obj, distinction='', name=None):
        """Get or create calendar for an object"""
        try:
            return self.get_calendar_for_object(obj, distinction)
        except Calendar.DoesNotExist:
            if name is None:
                calendar = self.model(name=str(obj))
            else:
                calendar = self.model(name=name)
            calendar.slug = slugify(calendar.name)
            calendar.save()
            calendar.create_relation(obj, distinction)
            return calendar

    def get_calendars_for_object(self, obj, distinction=''):
        """Get all calendars for a specific object"""
        ct = ContentType.objects.get_for_model(obj)
        if distinction:
            dist_q = models.Q(calendarrelation__distinction=distinction)
        else:
            dist_q = models.Q()
        return self.filter(
            dist_q, 
            calendarrelation__content_type=ct, 
            calendarrelation__object_id=obj.id
        )

class Calendar(TimeStampedModel):
    """
    Modernized calendar for grouping events with enhanced features
    """
    CALENDAR_TYPES = [
        ('project', 'Project Calendar'),
        ('worker', 'Worker Calendar'),
        ('company', 'Company Calendar'),
        ('department', 'Department Calendar'),
        ('maintenance', 'Maintenance Calendar'),
        ('training', 'Training Calendar'),
        ('holiday', 'Holiday Calendar'),
        ('custom', 'Custom Calendar'),
    ]

    COLOR_CHOICES = [
        ('#007bff', 'Blue'),
        ('#28a745', 'Green'),
        ('#dc3545', 'Red'),
        ('#ffc107', 'Yellow'),
        ('#17a2b8', 'Cyan'),
        ('#6f42c1', 'Purple'),
        ('#fd7e14', 'Orange'),
        ('#6c757d', 'Gray'),
        ('#343a40', 'Dark'),
        ('#e83e8c', 'Pink'),
    ]

    # Basic Information
    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    description = models.TextField(blank=True, help_text='Calendar description')
    calendar_type = models.CharField(
        max_length=20, 
        choices=CALENDAR_TYPES, 
        default='custom',
        help_text='Type of calendar'
    )
    
    # Visual Settings
    color = models.CharField(
        max_length=7, 
        choices=COLOR_CHOICES, 
        default='#007bff',
        help_text='Calendar display color'
    )
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text='FontAwesome icon class (e.g., fa-calendar)'
    )
    
    # Permissions and Visibility
    is_public = models.BooleanField(
        default=False,
        help_text='Whether this calendar is visible to all users'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this calendar is currently active'
    )
    
    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_calendars',
        help_text='Calendar owner'
    )
    
    # Settings
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text='Calendar timezone'
    )
    default_event_duration = models.DurationField(
        default=timedelta(hours=1),
        help_text='Default duration for new events'
    )
    
    # Workflow settings
    requires_approval = models.BooleanField(
        default=False,
        help_text='Whether events require approval'
    )
    auto_accept_events = models.BooleanField(
        default=True,
        help_text='Auto-accept events from trusted sources'
    )
    
    objects = CalendarManager()

    class Meta:
        verbose_name = _('calendar')
        verbose_name_plural = _('calendars')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def events(self):
        return self.event_set

    def create_relation(self, obj, distinction='', inheritable=True):
        """Creates a CalendarRelation between self and obj"""
        CalendarRelation.objects.create_relation(self, obj, distinction, inheritable)

    def get_events_for_date_range(self, start_date, end_date):
        """Get all events in date range"""
        return self.events.filter(
            start__date__gte=start_date,
            end__date__lte=end_date
        ).order_by('start')

    def get_upcoming_events(self, days=7):
        """Get upcoming events for next N days"""
        start = timezone.now()
        end = start + timedelta(days=days)
        return self.events.filter(
            start__gte=start,
            start__lt=end
        ).order_by('start')

    def get_absolute_url(self):
        return reverse('calendar-detail', kwargs={'slug': self.slug})

class CalendarRelationManager(models.Manager):
    def create_relation(self, calendar, content_object, distinction='', inheritable=True):
        """Creates a relation between calendar and content_object"""
        return CalendarRelation.objects.create(
            calendar=calendar,
            distinction=distinction,
            content_object=content_object,
            inheritable=inheritable
        )

class CalendarRelation(TimeStampedModel):
    """
    Modernized calendar relations with enhanced permissions
    """
    PERMISSION_LEVELS = [
        ('view', 'View Only'),
        ('contribute', 'Can Add Events'),
        ('edit', 'Can Edit Events'),
        ('manage', 'Can Manage Calendar'),
        ('admin', 'Full Admin Access'),
    ]

    calendar = models.ForeignKey(
        Calendar, 
        on_delete=models.CASCADE, 
        verbose_name=_("calendar")
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField(db_index=True)
    content_object = fields.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(_("distinction"), max_length=20, blank=True)
    inheritable = models.BooleanField(_("inheritable"), default=True)
    
    # Enhanced permissions
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_LEVELS,
        default='view',
        help_text='Permission level for this relation'
    )
    
    # Notification settings
    notify_on_changes = models.BooleanField(
        default=False,
        help_text='Send notifications when calendar changes'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('calendar relation')
        verbose_name_plural = _('calendar relations')
        unique_together = ['calendar', 'content_type', 'object_id', 'distinction']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.calendar} - {self.content_object} ({self.permission_level})'

class EventManager(models.Manager):
    def get_for_object(self, content_object, distinction='', inherit=True):
        """Get events for a specific object"""
        return EventRelation.objects.get_events_for_object(content_object, distinction, inherit)

    def upcoming(self, days=30):
        """Get upcoming events"""
        start = timezone.now()
        end = start + timedelta(days=days)
        return self.filter(start__gte=start, start__lt=end).order_by('start')

    def today(self):
        """Get today's events"""
        today = timezone.now().date()
        return self.filter(start__date=today).order_by('start')

    def for_worker(self, worker):
        """Get events for a specific worker"""
        return self.filter(
            models.Q(lead=worker) | 
            models.Q(workers=worker) |
            models.Q(creator=worker)
        ).distinct()

class Event(TimeStampedModel):
    """
    Modernized event model with enhanced features
    """
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('project_work', 'Project Work'),
        ('training', 'Training'),
        ('maintenance', 'Maintenance'),
        ('inspection', 'Inspection'),
        ('delivery', 'Delivery'),
        ('travel', 'Travel'),
        ('holiday', 'Holiday'),
        ('sick_leave', 'Sick Leave'),
        ('vacation', 'Vacation'),
        ('personal', 'Personal Time'),
        ('conference', 'Conference'),
        ('site_visit', 'Site Visit'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('tentative', 'Tentative'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('confidential', 'Confidential'),
    ]

    # Basic Information
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    event_type = models.CharField(
        max_length=20, 
        choices=EVENT_TYPES, 
        default='other',
        help_text='Type of event'
    )
    
    # Project and Work Details
    project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Associated project'
    )
    location = models.CharField(
        max_length=200, 
        blank=True,
        help_text='Event location'
    )
    
    # Legacy fields (keeping for compatibility)
    text = models.TextField(blank=True, null=True, help_text='Contractor notes')
    equip = models.TextField(blank=True, null=True, help_text='Equipment needed')
    details = models.TextField(blank=True, null=True, help_text='Additional details')
    
    # Time and Duration
    start = models.DateTimeField(_("start"), db_index=True)
    end = models.DateTimeField(
        _("end"), 
        db_index=True, 
        help_text=_("The end time must be later than the start time.")
    )
    all_day = models.BooleanField(
        default=False,
        help_text='Is this an all-day event?'
    )
    
    # Work scheduling fields
    start_time = models.TimeField(
        blank=True, 
        null=True, 
        help_text='Meet at the office time'
    )
    dist_time = models.TimeField(
        blank=True, 
        null=True, 
        help_text='Parts pickup time'
    )
    Supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        help_text='Parts Supplier'
    )
    
    # Staff Assignment
    lead = models.ForeignKey(
        Worker, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='led_events', 
        help_text='Event lead/supervisor'
    )
    workers = models.ManyToManyField(
        Worker, 
        blank=True, 
        related_name='assigned_events', 
        help_text='Assigned workers'
    )
    required_workers = models.PositiveIntegerField(
        default=1,
        help_text='Number of workers required'
    )
    
    # Status and Workflow
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='confirmed'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='normal'
    )
    privacy = models.CharField(
        max_length=15, 
        choices=PRIVACY_CHOICES, 
        default='public'
    )
    
    # Recurrence
    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("rule"),
        help_text=_("Select '----' for a one time only event.")
    )
    end_recurring_period = models.DateTimeField(
        _("end recurring period"), 
        null=True, 
        blank=True, 
        db_index=True,
        help_text=_("This date is ignored for one time only events.")
    )
    
    # Calendar Association
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        verbose_name=_("calendar")
    )
    
    # Visual and Display
    color_event = models.CharField(
        _("Event color"), 
        blank=True, 
        max_length=7,
        help_text='Hex color code for event display'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='FontAwesome icon class'
    )
    
    # Cost and Financial
    estimated_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated cost for this event'
    )
    actual_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Actual cost incurred'
    )
    
    # Reminders and Notifications
    reminder_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Send reminder X minutes before event'
    )
    send_invitations = models.BooleanField(
        default=False,
        help_text='Send email invitations to participants'
    )
    
    # Completion and Results
    completion_notes = models.TextField(
        blank=True,
        help_text='Notes about event completion'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the event was marked complete'
    )
    
    # File Attachments
    attachment = models.FileField(
        upload_to='events/attachments/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Event-related documents'
    )
    
    # System Fields
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("creator"),
        related_name='created_events'
    )
    
    # Integration fields
    external_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='External system ID for integration'
    )
    sync_status = models.CharField(
        max_length=20,
        blank=True,
        help_text='Synchronization status with external systems'
    )
    
    objects = EventManager()

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['start']
        indexes = [
            models.Index(fields=['start', 'end']),
            models.Index(fields=['calendar', 'start']),
            models.Index(fields=['project', 'start']),
            models.Index(fields=['status', 'start']),
        ]

    def __str__(self):
        return f'{self.title}: {self.start.strftime("%m/%d/%Y %H:%M")} - {self.end.strftime("%m/%d/%Y %H:%M")}'

    def clean(self):
        """Validate event data"""
        errors = {}
        
        if self.start and self.end:
            if self.start >= self.end:
                errors['end'] = 'End time must be after start time'
        
        # Validate all-day events
        if self.all_day:
            if self.start and self.start.time() != time.min:
                errors['start'] = 'All-day events should start at midnight'
        
        # Validate worker capacity
        if self.workers.count() > 0 and self.required_workers > 0:
            if self.workers.count() > self.required_workers * 2:  # Allow some flexibility
                errors['workers'] = f'Too many workers assigned (max recommended: {self.required_workers * 2})'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Set completion timestamp
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Clear completion timestamp if not completed
        if self.status != 'completed':
            self.completed_at = None
        
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """Get event duration as timedelta"""
        return self.end - self.start

    @property
    def duration_hours(self):
        """Get duration in hours as decimal"""
        total_seconds = self.duration.total_seconds()
        return Decimal(str(round(total_seconds / 3600, 2)))

    @property
    def is_past(self):
        """Check if event is in the past"""
        return self.end < timezone.now()

    @property
    def is_current(self):
        """Check if event is currently happening"""
        now = timezone.now()
        return self.start <= now <= self.end

    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        return self.start > timezone.now()

    @property
    def is_overdue(self):
        """Check if event is overdue (past end time and not completed)"""
        return self.is_past and self.status not in ['completed', 'cancelled']

    @property
    def worker_count(self):
        """Get number of assigned workers"""
        return self.workers.count()

    @property
    def is_fully_staffed(self):
        """Check if event has enough workers assigned"""
        return self.worker_count >= self.required_workers

    @property
    def cost_variance(self):
        """Calculate cost variance (actual - estimated)"""
        if self.estimated_cost and self.actual_cost:
            return self.actual_cost - self.estimated_cost
        return None

    def get_absolute_url(self):
        return reverse('event-detail', args=[self.id])

    def can_edit(self, user):
        """Check if user can edit this event"""
        if user == self.creator:
            return True
        if user == self.lead:
            return True
        # Check calendar permissions
        relation = CalendarRelation.objects.filter(
            calendar=self.calendar,
            content_type=ContentType.objects.get_for_model(user),
            object_id=user.id,
            permission_level__in=['edit', 'manage', 'admin']
        ).first()
        return relation is not None

    def get_worker_list(self):
        """Get formatted list of assigned workers"""
        workers = list(self.workers.all())
        if self.lead and self.lead not in workers:
            workers.insert(0, self.lead)
        return workers

    def mark_completed(self, completion_notes=''):
        """Mark event as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if completion_notes:
            self.completion_notes = completion_notes
        self.save()

class EventRelationManager(models.Manager):
    def get_events_for_object(self, content_object, distinction='', inherit=True):
        """Get events for a specific object with optional inheritance"""
        ct = ContentType.objects.get_for_model(type(content_object))
        
        if distinction:
            dist_q = models.Q(eventrelation__distinction=distinction)
            cal_dist_q = models.Q(calendar__calendarrelation__distinction=distinction)
        else:
            dist_q = models.Q()
            cal_dist_q = models.Q()
        
        if inherit:
            inherit_q = models.Q(
                cal_dist_q,
                calendar__calendarrelation__content_type=ct,
                calendar__calendarrelation__object_id=content_object.id,
                calendar__calendarrelation__inheritable=True,
            )
        else:
            inherit_q = models.Q()
        
        event_q = models.Q(
            dist_q, 
            eventrelation__content_type=ct, 
            eventrelation__object_id=content_object.id
        )
        
        return Event.objects.filter(inherit_q | event_q)

    def create_relation(self, event, content_object, distinction=''):
        """Create a relation between event and content_object"""
        return EventRelation.objects.create(
            event=event,
            distinction=distinction,
            content_object=content_object
        )

class EventRelation(TimeStampedModel):
    """
    Enhanced event relations with additional metadata
    """
    RELATION_TYPES = [
        ('attendee', 'Attendee'),
        ('organizer', 'Organizer'),
        ('resource', 'Resource'),
        ('location', 'Location'),
        ('viewer', 'Viewer'),
        ('participant', 'Participant'),
        ('observer', 'Observer'),
    ]

    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        verbose_name=_("event")
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField(db_index=True)
    content_object = fields.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(
        _("distinction"), 
        max_length=20,
        choices=RELATION_TYPES,
        default='participant'
    )
    
    # RSVP and Response
    response_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
            ('tentative', 'Tentative'),
        ],
        default='pending',
        help_text='Response to event invitation'
    )
    
    # Participation details
    is_required = models.BooleanField(
        default=False,
        help_text='Is participation required?'
    )
    send_notifications = models.BooleanField(
        default=True,
        help_text='Send notifications to this participant'
    )
    
    objects = EventRelationManager()

    class Meta:
        verbose_name = _("event relation")
        verbose_name_plural = _("event relations")
        unique_together = ['event', 'content_type', 'object_id', 'distinction']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.event.title}({self.distinction})-{self.content_object}'

class Occurrence(TimeStampedModel):
    """
    Modernized occurrence model for recurring events
    """
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        verbose_name=_("event")
    )
    title = models.CharField(_("title"), max_length=255, blank=True)
    description = models.TextField(_("description"), blank=True)
    start = models.DateTimeField(_("start"), db_index=True)
    end = models.DateTimeField(_("end"), db_index=True)
    cancelled = models.BooleanField(_("cancelled"), default=False)
    original_start = models.DateTimeField(_("original start"))
    original_end = models.DateTimeField(_("original end"))
    
    # Additional fields for enhanced functionality
    notes = models.TextField(blank=True, help_text='Notes specific to this occurrence')
    status_override = models.CharField(
        max_length=20,
        blank=True,
        help_text='Override status for this specific occurrence'
    )

    class Meta:
        verbose_name = _("occurrence")
        verbose_name_plural = _("occurrences")
        ordering = ['start']
        indexes = [
            models.Index(fields=['start', 'end']),
            models.Index(fields=['event', 'start']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.title and self.event_id:
            self.title = self.event.title
        if not self.description and self.event_id:
            self.description = self.event.description

    def __str__(self):
        return f"{self.title}: {self.start.strftime('%m/%d/%Y %H:%M')} - {self.end.strftime('%m/%d/%Y %H:%M')}"

    @property
    def moved(self):
        """Check if occurrence has been moved from original time"""
        return self.original_start != self.start or self.original_end != self.end

    @property
    def duration(self):
        """Get occurrence duration"""
        return self.end - self.start

    @property
    def duration_hours(self):
        """Get duration in hours"""
        return self.duration.total_seconds() / 3600

    def move(self, new_start, new_end):
        """Move occurrence to new time"""
        self.start = new_start
        self.end = new_end
        self.save()

    def cancel(self):
        """Cancel this occurrence"""
        self.cancelled = True
        self.save()

    def uncancel(self):
        """Uncancel this occurrence"""
        self.cancelled = False
        self.save()

    def get_absolute_url(self):
        if self.pk is not None:
            return reverse('occurrence-detail', kwargs={
                'occurrence_id': self.pk,
                'event_id': self.event.id
            })
        return reverse('occurrence-by-date', kwargs={
            'event_id': self.event.id,
            'year': self.start.year,
            'month': self.start.month,
            'day': self.start.day,
            'hour': self.start.hour,
            'minute': self.start.minute,
            'second': self.start.second,
        })
