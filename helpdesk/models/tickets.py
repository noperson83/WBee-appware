# helpdesk/models/tickets.py - Ticket and Related Models

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

class TicketManager(models.Manager):
    def open(self):
        """Get open tickets"""
        return self.filter(status__in=[Ticket.OPEN_STATUS, Ticket.REOPENED_STATUS])

    def closed(self):
        """Get closed tickets"""
        return self.filter(status__in=[Ticket.RESOLVED_STATUS, Ticket.CLOSED_STATUS])

    def unassigned(self):
        """Get unassigned tickets"""
        return self.filter(assigned_to__isnull=True)

    def overdue(self):
        """Get overdue tickets"""
        return self.filter(
            due_date__lt=timezone.now(),
            status__in=[Ticket.OPEN_STATUS, Ticket.REOPENED_STATUS]
        )

    def high_priority(self):
        """Get high priority tickets"""
        return self.filter(priority__in=[1, 2])

    def for_user(self, user):
        """Get tickets assigned to or submitted by user"""
        return self.filter(
            models.Q(assigned_to=user) | 
            models.Q(submitter_email=user.email)
        )

class Ticket(models.Model):
    """
    Modernized ticket model with enhanced tracking and workflow
    """
    # Status Constants
    OPEN_STATUS = 1
    REOPENED_STATUS = 2
    RESOLVED_STATUS = 3
    CLOSED_STATUS = 4
    DUPLICATE_STATUS = 5
    ON_HOLD_STATUS = 6
    PENDING_STATUS = 7

    STATUS_CHOICES = [
        (OPEN_STATUS, _('Open')),
        (REOPENED_STATUS, _('Reopened')),
        (RESOLVED_STATUS, _('Resolved')),
        (CLOSED_STATUS, _('Closed')),
        (DUPLICATE_STATUS, _('Duplicate')),
        (ON_HOLD_STATUS, _('On Hold')),
        (PENDING_STATUS, _('Pending Customer')),
    ]

    PRIORITY_CHOICES = [
        (1, _('1. Critical')),
        (2, _('2. High')),
        (3, _('3. Normal')),
        (4, _('4. Low')),
        (5, _('5. Very Low')),
    ]

    TICKET_TYPES = [
        ('bug', _('Bug Report')),
        ('feature', _('Feature Request')),
        ('support', _('Support Request')),
        ('question', _('Question')),
        ('incident', _('Incident')),
        ('change', _('Change Request')),
        ('maintenance', _('Maintenance')),
        ('other', _('Other')),
    ]

    URGENCY_CHOICES = [
        (1, _('Critical - System Down')),
        (2, _('High - Major Impact')),
        (3, _('Medium - Some Impact')),
        (4, _('Low - Minor Impact')),
        (5, _('Planning - No Impact')),
    ]

    # Basic Information
    title = models.CharField(
        _('Title'),
        max_length=200,
        help_text=_('Brief description of the issue')
    )
    queue = models.ForeignKey(
        'base.Queue',
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('Queue')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        null=True,
        help_text=_('The content of the customer\'s query.')
    )
    ticket_type = models.CharField(
        _('Ticket Type'),
        max_length=20,
        choices=TICKET_TYPES,
        default='support',
        help_text=_('What type of request is this?')
    )

    # UUID for external references
    uuid = models.UUIDField(
        _('UUID'),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_('Unique identifier for API and external integrations')
    )

    # Submitter Information
    submitter_email = models.EmailField(
        _('Submitter E-Mail'),
        blank=True,
        null=True,
        help_text=_('The submitter will receive an email for all public follow-ups.')
    )
    submitter_name = models.CharField(
        _('Submitter Name'),
        max_length=100,
        blank=True,
        help_text=_('Name of the person who submitted this ticket')
    )
    submitter_phone = models.CharField(
        _('Submitter Phone'),
        max_length=20,
        blank=True,
        help_text=_('Phone number of the submitter')
    )
    submitter_organization = models.CharField(
        _('Organization'),
        max_length=100,
        blank=True,
        help_text=_('Organization the submitter belongs to')
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        blank=True,
        null=True,
        verbose_name=_('Assigned to')
    )
    assigned_date = models.DateTimeField(
        _('Assigned Date'),
        blank=True,
        null=True,
        help_text=_('When this ticket was assigned to current user')
    )

    # Status and Priority
    status = models.IntegerField(
        _('Status'),
        choices=STATUS_CHOICES,
        default=OPEN_STATUS
    )
    priority = models.IntegerField(
        _('Priority'),
        choices=PRIORITY_CHOICES,
        default=3,
        help_text=_('1 = Highest Priority, 5 = Low Priority')
    )
    urgency = models.IntegerField(
        _('Urgency'),
        choices=URGENCY_CHOICES,
        default=3,
        help_text=_('Business impact of this issue')
    )

    # Workflow Control
    on_hold = models.BooleanField(
        _('On Hold'),
        default=False,
        help_text=_('If a ticket is on hold, it will not automatically be escalated.')
    )
    hold_reason = models.TextField(
        _('Hold Reason'),
        blank=True,
        help_text=_('Reason why this ticket is on hold')
    )

    # Resolution
    resolution = models.TextField(
        _('Resolution'),
        blank=True,
        null=True,
        help_text=_('The resolution provided to the customer by our staff.')
    )
    resolution_date = models.DateTimeField(
        _('Resolution Date'),
        blank=True,
        null=True,
        help_text=_('When this ticket was resolved')
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='closed_tickets',
        blank=True,
        null=True,
        verbose_name=_('Closed by')
    )

    # Time Tracking
    created = models.DateTimeField(
        _('Created'),
        help_text=_('Date this ticket was first created')
    )
    modified = models.DateTimeField(
        _('Modified'),
        help_text=_('Date this ticket was most recently changed.')
    )
    due_date = models.DateTimeField(
        _('Due Date'),
        blank=True,
        null=True,
        help_text=_('When this ticket should be resolved')
    )
    first_response_date = models.DateTimeField(
        _('First Response Date'),
        blank=True,
        null=True,
        help_text=_('When the first response was sent to the customer')
    )

    # Escalation
    last_escalation = models.DateTimeField(
        _('Last Escalation'),
        blank=True,
        null=True,
        editable=False,
        help_text=_('The date this ticket was last escalated')
    )
    escalation_level = models.PositiveIntegerField(
        _('Escalation Level'),
        default=0,
        help_text=_('How many times this ticket has been escalated')
    )

    # Customer Satisfaction
    satisfaction_rating = models.PositiveIntegerField(
        _('Satisfaction Rating'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Customer satisfaction rating (1-5 stars)')
    )
    satisfaction_comment = models.TextField(
        _('Satisfaction Comment'),
        blank=True,
        help_text=_('Customer feedback about the resolution')
    )

    # Time Spent
    time_spent = models.DurationField(
        _('Time Spent'),
        blank=True,
        null=True,
        help_text=_('Total time spent working on this ticket')
    )
    billable_time = models.DurationField(
        _('Billable Time'),
        blank=True,
        null=True,
        help_text=_('Billable time for this ticket')
    )

    # Location and Environment
    location = models.CharField(
        _('Location'),
        max_length=100,
        blank=True,
        help_text=_('Physical location where issue occurred')
    )
    environment = models.CharField(
        _('Environment'),
        max_length=50,
        blank=True,
        help_text=_('Environment where issue occurred (prod, test, dev)')
    )

    # Additional Fields
    tags = models.CharField(
        _('Tags'),
        max_length=500,
        blank=True,
        help_text=_('Comma-separated tags for categorization')
    )
    external_reference = models.CharField(
        _('External Reference'),
        max_length=100,
        blank=True,
        help_text=_('Reference number from external system')
    )
    
    # Custom Fields
    custom_fields = models.JSONField(
        _('Custom Fields'),
        default=dict,
        blank=True,
        help_text=_('JSON field for custom ticket data')
    )

    objects = TicketManager()

    class Meta:
        get_latest_by = "created"
        ordering = ('-created',)
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['queue', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'{self.id} {self.title}'

    def clean(self):
        """Validate ticket data"""
        errors = {}
        
        if self.due_date and self.due_date <= timezone.now():
            if self.status in [self.OPEN_STATUS, self.REOPENED_STATUS]:
                pass  # Allow past due dates for open tickets (they become overdue)
        
        if self.resolution and not self.resolution_date:
            if self.status in [self.RESOLVED_STATUS, self.CLOSED_STATUS]:
                errors['resolution_date'] = _('Resolution date is required when ticket is resolved/closed')
        
        if self.satisfaction_rating and not self.resolution_date:
            errors['satisfaction_rating'] = _('Cannot rate satisfaction on unresolved ticket')
        
        if errors:
            raise ValidationError(errors)
        
class TicketDependency(models.Model):
    """
    Ticket dependency relationships - blocking/blocked by
    """
    DEPENDENCY_TYPES = [
        ('blocks', _('Blocks')),
        ('blocked_by', _('Blocked By')),
        ('relates_to', _('Relates To')),
        ('duplicates', _('Duplicates')),
        ('duplicated_by', _('Duplicated By')),
        ('child_of', _('Child Of')),
        ('parent_of', _('Parent Of')),
    ]

    # The ticket that has the dependency
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='dependencies',
        verbose_name=_('Ticket')
    )
    
    # The ticket this depends on
    depends_on = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='dependents',
        verbose_name=_('Depends On')
    )
    
    # Type of dependency
    dependency_type = models.CharField(
        _('Dependency Type'),
        max_length=20,
        choices=DEPENDENCY_TYPES,
        default='blocks',
        help_text=_('How these tickets are related')
    )
    
    # Additional information
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional information about this dependency')
    )
    
    # Timestamps
    created = models.DateTimeField(
        _('Created'),
        auto_now_add=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Created By')
    )

    class Meta:
        unique_together = ['ticket', 'depends_on', 'dependency_type']
        verbose_name = _('Ticket Dependency')
        verbose_name_plural = _('Ticket Dependencies')
        ordering = ['created']

    def __str__(self):
        return f'{self.ticket} {self.dependency_type} {self.depends_on}'

    def clean(self):
        """Validate dependency"""
        if self.ticket == self.depends_on:
            raise ValidationError(_('A ticket cannot depend on itself'))

class TicketCC(models.Model):
    """
    CC (Carbon Copy) recipients for ticket notifications
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='cc_list',
        verbose_name=_('Ticket')
    )
    
    # User or email for CC
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('User'),
        help_text=_('User to CC on ticket updates')
    )
    
    email = models.EmailField(
        _('Email'),
        blank=True,
        help_text=_('Email address to CC (if not a system user)')
    )
    
    # Notification preferences
    can_view = models.BooleanField(
        _('Can View'),
        default=True,
        help_text=_('Can this person view the ticket?')
    )
    
    can_update = models.BooleanField(
        _('Can Update'),
        default=False,
        help_text=_('Can this person update the ticket?')
    )
    
    # Control what notifications to send
    notify_on_new_followup = models.BooleanField(
        _('Notify on New Follow-up'),
        default=True,
        help_text=_('Send notifications when new follow-ups are added')
    )
    
    notify_on_status_change = models.BooleanField(
        _('Notify on Status Change'),
        default=True,
        help_text=_('Send notifications when ticket status changes')
    )
    
    notify_on_assignment = models.BooleanField(
        _('Notify on Assignment'),
        default=True,
        help_text=_('Send notifications when ticket is assigned/reassigned')
    )
    
    # Metadata
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='added_cc_entries',
        null=True,
        blank=True,
        verbose_name=_('Added By')
    )
    
    added_date = models.DateTimeField(
        _('Added Date'),
        auto_now_add=True
    )
    
    notes = models.CharField(
        _('Notes'),
        max_length=200,
        blank=True,
        help_text=_('Why this person was added to CC')
    )

    class Meta:
        unique_together = ['ticket', 'user', 'email']
        verbose_name = _('Ticket CC')
        verbose_name_plural = _('Ticket CCs')
        ordering = ['added_date']

    def __str__(self):
        if self.user:
            return f'{self.ticket} CC: {self.user}'
        else:
            return f'{self.ticket} CC: {self.email}'

    def clean(self):
        """Validate CC entry"""
        if not self.user and not self.email:
            raise ValidationError(_('Either user or email must be specified'))
        
        if self.user and self.email:
            # If both are provided, make sure email matches user's email
            if self.user.email != self.email:
                raise ValidationError(_('Email must match the selected user\'s email'))

    @property
    def recipient_email(self):
        """Get the email address for this CC entry"""
        if self.user:
            return self.user.email
        return self.email

    @property
    def recipient_name(self):
        """Get the display name for this CC entry"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.email
