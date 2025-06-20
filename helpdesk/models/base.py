# helpdesk/models/base.py - Base Models and Managers

from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from datetime import datetime, timedelta
import re

from hr.models import Worker

class QueueManager(models.Manager):
    def active(self):
        """Get active queues only"""
        return self.filter(is_active=True)

    def public_submission_enabled(self):
        """Get queues that allow public submission"""
        return self.filter(allow_public_submission=True, is_active=True)

    def email_enabled(self):
        """Get queues with email submission enabled"""
        return self.filter(allow_email_submission=True, is_active=True)

class Queue(models.Model):
    """
    Modernized queue model with enhanced features and better organization
    """
    ESCALATION_TYPES = [
        ('none', _('No Escalation')),
        ('time_based', _('Time-Based Escalation')),
        ('priority_based', _('Priority-Based Escalation')),
        ('sla_based', _('SLA-Based Escalation')),
    ]

    EMAIL_BOX_TYPES = [
        ('pop3', _('POP3')),
        ('imap', _('IMAP')),
        ('local', _('Local Directory')),
        ('exchange', _('Microsoft Exchange')),
        ('oauth', _('OAuth (Gmail/Outlook)')),
    ]

    SOCKS_PROXY_TYPES = [
        ('socks4', _('SOCKS4')),
        ('socks5', _('SOCKS5')),
    ]

    LOGGING_LEVELS = [
        ('none', _('None')),
        ('debug', _('Debug')),
        ('info', _('Information')),
        ('warn', _('Warning')),
        ('error', _('Error')),
        ('crit', _('Critical'))
    ]

    # Basic Information
    title = models.CharField(
        _('Title'),
        max_length=100,
        help_text=_('Display name for this queue')
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=50,
        unique=True,
        help_text=_('This slug is used when building ticket IDs. Once set, try not to change it or e-mailing may get messy.')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Internal description of this queue\'s purpose')
    )
    
    # Status and Visibility
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this queue is currently accepting tickets')
    )
    is_public = models.BooleanField(
        _('Public Queue'),
        default=False,
        help_text=_('Whether this queue appears in public lists')
    )
    
    # Email Configuration
    email_address = models.EmailField(
        _('E-Mail Address'),
        blank=True,
        null=True,
        help_text=_('All outgoing e-mails for this queue will use this e-mail address.')
    )
    from_name = models.CharField(
        _('From Name'),
        max_length=100,
        blank=True,
        help_text=_('Display name for outgoing emails (e.g., "Support Team")')
    )
    
    # Localization
    locale = models.CharField(
        _('Locale'),
        max_length=10,
        blank=True,
        null=True,
        help_text=_('Locale of this queue. All correspondence will be in this language.')
    )
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='UTC',
        help_text=_('Timezone for this queue\'s operations')
    )

    # Submission Settings
    allow_public_submission = models.BooleanField(
        _('Allow Public Submission?'),
        default=False,
        help_text=_('Should this queue be listed on the public submission form?')
    )
    allow_email_submission = models.BooleanField(
        _('Allow E-Mail Submission?'),
        default=False,
        help_text=_('Do you want to poll the e-mail box below for new tickets?')
    )
    allow_api_submission = models.BooleanField(
        _('Allow API Submission?'),
        default=False,
        help_text=_('Allow ticket creation via REST API')
    )
    require_registration = models.BooleanField(
        _('Require Registration'),
        default=False,
        help_text=_('Require users to register before submitting tickets')
    )

    # SLA and Escalation
    escalation_type = models.CharField(
        _('Escalation Type'),
        max_length=20,
        choices=ESCALATION_TYPES,
        default='time_based',
        help_text=_('How should tickets in this queue be escalated?')
    )
    escalate_days = models.IntegerField(
        _('Escalation Days'),
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        help_text=_('For tickets which are not held, how often do you wish to increase their priority? Set to 0 for no escalation.')
    )
    sla_response_time = models.DurationField(
        _('SLA Response Time'),
        null=True,
        blank=True,
        help_text=_('Maximum time to first response (e.g., "2:00:00" for 2 hours)')
    )
    sla_resolution_time = models.DurationField(
        _('SLA Resolution Time'),
        null=True,
        blank=True,
        help_text=_('Maximum time to resolution (e.g., "1 00:00:00" for 1 day)')
    )

    # Notifications
    new_ticket_cc = models.CharField(
        _('New Ticket CC Address'),
        blank=True,
        null=True,
        max_length=500,
        help_text=_('Email addresses to notify of new tickets (comma-separated)')
    )
    updated_ticket_cc = models.CharField(
        _('Updated Ticket CC Address'),
        blank=True,
        null=True,
        max_length=500,
        help_text=_('Email addresses to notify of ticket updates (comma-separated)')
    )
    send_sms_notifications = models.BooleanField(
        _('Send SMS Notifications'),
        default=False,
        help_text=_('Send SMS notifications for critical tickets')
    )

    # Email Box Configuration
    email_box_type = models.CharField(
        _('E-Mail Box Type'),
        max_length=10,
        choices=EMAIL_BOX_TYPES,
        blank=True,
        null=True,
        help_text=_('E-Mail server type for creating tickets automatically from a mailbox')
    )
    email_box_host = models.CharField(
        _('E-Mail Hostname'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Your e-mail server address - either domain name or IP address')
    )
    email_box_port = models.IntegerField(
        _('E-Mail Port'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        help_text=_('Port number to use for accessing e-mail')
    )
    email_box_ssl = models.BooleanField(
        _('Use SSL for E-Mail?'),
        default=False,
        help_text=_('Whether to use SSL for IMAP or POP3')
    )
    email_box_user = models.CharField(
        _('E-Mail Username'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Username for accessing this mailbox')
    )
    email_box_pass = models.CharField(
        _('E-Mail Password'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('Password for the above username (encrypted in database)')
    )
    email_box_imap_folder = models.CharField(
        _('IMAP Folder'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('IMAP folder to fetch messages from. Default: INBOX')
    )
    email_box_local_dir = models.CharField(
        _('E-Mail Local Directory'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('Local directory path to poll for new email')
    )
    email_box_interval = models.IntegerField(
        _('E-Mail Check Interval'),
        help_text=_('How often to check mailbox (in minutes)'),
        blank=True,
        null=True,
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )
    email_box_last_check = models.DateTimeField(
        _('Last Email Check'),
        blank=True,
        null=True,
        editable=False
    )

    # Security and Proxy
    socks_proxy_type = models.CharField(
        _('Socks Proxy Type'),
        max_length=8,
        choices=SOCKS_PROXY_TYPES,
        blank=True,
        null=True,
        help_text=_('SOCKS proxy type for connections')
    )
    socks_proxy_host = models.GenericIPAddressField(
        _('Socks Proxy Host'),
        blank=True,
        null=True,
        help_text=_('Socks proxy IP address. Default: 127.0.0.1')
    )
    socks_proxy_port = models.IntegerField(
        _('Socks Proxy Port'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        help_text=_('Socks proxy port number. Default: 9150')
    )

    # Logging
    logging_type = models.CharField(
        _('Logging Type'),
        max_length=5,
        choices=LOGGING_LEVELS,
        blank=True,
        null=True,
        help_text=_('Default logging level for this queue')
    )
    logging_dir = models.CharField(
        _('Logging Directory'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('Directory for log files. Default: /var/log/helpdesk/')
    )

    # Staff Assignment
    default_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='default_owned_queues',
        blank=True,
        null=True,
        verbose_name=_('Default owner'),
        help_text=_('Default assignee for new tickets in this queue')
    )
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='managed_queues',
        help_text=_('Users who can manage this queue')
    )
    
    # Business Logic
    auto_assign = models.BooleanField(
        _('Auto-assign Tickets'),
        default=False,
        help_text=_('Automatically assign new tickets to available staff')
    )
    require_approval = models.BooleanField(
        _('Require Approval'),
        default=False,
        help_text=_('Require supervisor approval before closing tickets')
    )
    
    # Custom Fields
    custom_fields = models.JSONField(
        _('Custom Queue Settings'),
        default=dict,
        blank=True,
        help_text=_('JSON field for custom queue-specific settings')
    )

    # System Fields
    permission_name = models.CharField(
        _('Django auth permission name'),
        max_length=72,
        blank=True,
        null=True,
        editable=False,
        help_text=_('Name used in the django.contrib.auth permission system')
    )
    created_at = models.DateTimeField(_('Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated'), auto_now=True)

    objects = QueueManager()

    class Meta:
        ordering = ('title',)
        verbose_name = _('Queue')
        verbose_name_plural = _('Queues')
        indexes = [
            models.Index(fields=['is_active', 'allow_public_submission']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """Validate queue data"""
        errors = {}
        
        # Validate email settings
        if self.allow_email_submission:
            if not self.email_box_type:
                errors['email_box_type'] = _('Email box type is required when email submission is enabled')
            if not self.email_box_host and self.email_box_type not in ['local', 'oauth']:
                errors['email_box_host'] = _('Email host is required for this email box type')
            if not self.email_box_user and self.email_box_type not in ['local']:
                errors['email_box_user'] = _('Email username is required for this email box type')
        
        # Validate SLA settings
        if self.sla_response_time and self.sla_resolution_time:
            if self.sla_response_time >= self.sla_resolution_time:
                errors['sla_resolution_time'] = _('Resolution time must be longer than response time')
        
        # Validate escalation settings
        if self.escalation_type != 'none' and not self.escalate_days:
            errors['escalate_days'] = _('Escalation days is required when escalation is enabled')
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Set default IMAP folder
        if self.email_box_type == 'imap' and not self.email_box_imap_folder:
            self.email_box_imap_folder = 'INBOX'

        # Set default proxy settings
        if self.socks_proxy_type:
            if not self.socks_proxy_host:
                self.socks_proxy_host = '127.0.0.1'
            if not self.socks_proxy_port:
                self.socks_proxy_port = 9150
        else:
            self.socks_proxy_host = None
            self.socks_proxy_port = None

        # Set default email ports
        if not self.email_box_port and self.email_box_type:
            if self.email_box_type == 'imap':
                self.email_box_port = 993 if self.email_box_ssl else 143
            elif self.email_box_type == 'pop3':
                self.email_box_port = 995 if self.email_box_ssl else 110

        # Create permission for new queue
        if not self.id:
            basename = self.prepare_permission_name()
            Permission.objects.get_or_create(
                name=_("Permission for queue: ") + self.title,
                content_type=ContentType.objects.get_for_model(self.__class__),
                codename=basename,
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        permission_name = self.permission_name
        super().delete(*args, **kwargs)

        # Remove permission when queue is deleted
        if permission_name:
            try:
                p = Permission.objects.get(codename=permission_name[9:])
                p.delete()
            except ObjectDoesNotExist:
                pass

    @property
    def from_address(self):
        """Short property to provide a sender address in SMTP format"""
        if not self.email_address:
            default_email = re.match(".*<(?P<email>.*@*.)>", settings.DEFAULT_FROM_EMAIL)
            if default_email is not None:
                return f'NO QUEUE EMAIL ADDRESS DEFINED {settings.DEFAULT_FROM_EMAIL}'
            else:
                return f'NO QUEUE EMAIL ADDRESS DEFINED <{settings.DEFAULT_FROM_EMAIL}>'
        else:
            from_name = self.from_name or self.title
            return f'{from_name} <{self.email_address}>'

    @property
    def ticket_count(self):
        """Total number of tickets in this queue"""
        return self.tickets.count()

    @property
    def open_ticket_count(self):
        """Number of open tickets in this queue"""
        from .tickets import Ticket
        return self.tickets.filter(status__in=[Ticket.OPEN_STATUS, Ticket.REOPENED_STATUS]).count()

    @property
    def average_resolution_time(self):
        """Average time to resolve tickets in this queue"""
        from .tickets import Ticket
        resolved_tickets = self.tickets.filter(
            status=Ticket.RESOLVED_STATUS,
            resolution_date__isnull=False
        )
        if not resolved_tickets.exists():
            return None
        
        total_time = timedelta()
        count = 0
        for ticket in resolved_tickets:
            if ticket.created and ticket.resolution_date:
                total_time += ticket.resolution_date - ticket.created
                count += 1
        
        return total_time / count if count > 0 else None

    @property
    def sla_compliance_rate(self):
        """Percentage of tickets meeting SLA requirements"""
        if not self.sla_resolution_time:
            return None
        
        from .tickets import Ticket
        total_tickets = self.tickets.filter(
            status__in=[Ticket.RESOLVED_STATUS, Ticket.CLOSED_STATUS]
        ).count()
        
        if total_tickets == 0:
            return 100
        
        compliant_tickets = 0
        for ticket in self.tickets.filter(status__in=[Ticket.RESOLVED_STATUS, Ticket.CLOSED_STATUS]):
            if ticket.resolution_time and ticket.resolution_time <= self.sla_resolution_time:
                compliant_tickets += 1
        
        return (compliant_tickets / total_tickets) * 100

    def prepare_permission_name(self):
        """Prepare internally the codename for the permission and store it in permission_name"""
        basename = f"queue_access_{self.slug}"
        self.permission_name = f"helpdesk.{basename}"
        return basename

    def get_absolute_url(self):
        return reverse('helpdesk:queue_detail', kwargs={'slug': self.slug})
