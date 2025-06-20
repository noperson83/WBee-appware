# helpdesk/models/utils.py - Utility Models (Saved Searches, User Settings, Ignore Rules, Custom Fields)

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import re

class SavedSearch(models.Model):
    """
    Enhanced saved searches with sharing and scheduling
    """
    SEARCH_TYPES = [
        ('ticket', _('Ticket Search')),
        ('kb', _('Knowledge Base Search')),
        ('user', _('User Search')),
        ('queue', _('Queue Search')),
        ('report', _('Report Query')),
    ]

    # Basic Information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    title = models.CharField(
        _('Query Name'),
        max_length=100,
        help_text=_('User-provided name for this query')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of what this search does')
    )
    search_type = models.CharField(
        _('Search Type'),
        max_length=20,
        choices=SEARCH_TYPES,
        default='ticket',
        help_text=_('Type of search this query performs')
    )

    # Sharing
    shared = models.BooleanField(
        _('Shared With Other Users?'),
        default=False,
        help_text=_('Should other users see this query?')
    )
    shared_with_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        help_text=_('Specific groups this search is shared with')
    )

    # Query Data
    query = models.TextField(
        _('Search Query'),
        help_text=_('Pickled query object. Be wary changing this.')
    )
    query_params = models.JSONField(
        _('Query Parameters'),
        default=dict,
        blank=True,
        help_text=_('JSON representation of search parameters')
    )

    # Automation
    is_alert = models.BooleanField(
        _('Email Alert'),
        default=False,
        help_text=_('Send email when this search has new results')
    )
    alert_frequency = models.CharField(
        _('Alert Frequency'),
        max_length=20,
        choices=[
            ('immediate', _('Immediate')),
            ('hourly', _('Hourly')),
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
        ],
        blank=True,
        help_text=_('How often to check for new results')
    )
    last_run = models.DateTimeField(
        _('Last Run'),
        blank=True,
        null=True,
        help_text=_('When this search was last executed')
    )

    # System Fields
    created_at = models.DateTimeField(_('Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated'), auto_now=True)

    class Meta:
        verbose_name = _('Saved search')
        verbose_name_plural = _('Saved searches')
        ordering = ['-updated_at']

    def __str__(self):
        if self.shared:
            return f'{self.title} (*)'
        else:
            return self.title

class UserSettings(models.Model):
    """
    Enhanced user settings with better organization
    """
    NOTIFICATION_PREFERENCES = [
        ('email', _('Email Only')),
        ('sms', _('SMS Only')),
        ('both', _('Email and SMS')),
        ('none', _('No Notifications')),
    ]

    THEME_CHOICES = [
        ('light', _('Light Theme')),
        ('dark', _('Dark Theme')),
        ('auto', _('Auto (System Preference)')),
    ]

    # Basic Relationship
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="helpdesk_settings"
    )

    # Display Preferences
    items_per_page = models.PositiveIntegerField(
        _('Items Per Page'),
        default=25,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        help_text=_('Number of items to show per page in lists')
    )
    theme = models.CharField(
        _('Theme'),
        max_length=10,
        choices=THEME_CHOICES,
        default='auto',
        help_text=_('Visual theme preference')
    )
    default_queue = models.ForeignKey(
        'base.Queue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('Default queue for new tickets')
    )

    # Notification Settings
    notification_preference = models.CharField(
        _('Notification Preference'),
        max_length=10,
        choices=NOTIFICATION_PREFERENCES,
        default='email',
        help_text=_('How you prefer to receive notifications')
    )
    notify_assigned = models.BooleanField(
        _('Notify When Assigned'),
        default=True,
        help_text=_('Receive notifications when tickets are assigned to you')
    )
    notify_updated = models.BooleanField(
        _('Notify When Updated'),
        default=True,
        help_text=_('Receive notifications when your tickets are updated')
    )
    notify_closed = models.BooleanField(
        _('Notify When Closed'),
        default=False,
        help_text=_('Receive notifications when your tickets are closed')
    )
    notify_escalated = models.BooleanField(
        _('Notify When Escalated'),
        default=True,
        help_text=_('Receive notifications when tickets are escalated')
    )

    # Dashboard Settings
    show_dashboard_stats = models.BooleanField(
        _('Show Dashboard Statistics'),
        default=True,
        help_text=_('Display statistics widgets on dashboard')
    )
    show_recent_activity = models.BooleanField(
        _('Show Recent Activity'),
        default=True,
        help_text=_('Display recent activity feed on dashboard')
    )

    # Contact Information
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20,
        blank=True,
        help_text=_('Phone number for SMS notifications')
    )
    slack_user_id = models.CharField(
        _('Slack User ID'),
        max_length=50,
        blank=True,
        help_text=_('Slack user ID for Slack notifications')
    )

    # Legacy Settings (for backward compatibility)
    settings_pickled = models.TextField(
        _('Legacy Settings Dictionary'),
        help_text=_('This is a base64-encoded representation of a pickled Python dictionary. Do not change this field via the admin.'),
        blank=True,
        null=True,
    )

    # System Fields
    created_at = models.DateTimeField(_('Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated'), auto_now=True)

    class Meta:
        verbose_name = _('User Setting')
        verbose_name_plural = _('User Settings')

    def __str__(self):
        return f'Preferences for {self.user}'

    # Legacy property for backward compatibility
    @property
    def settings(self):
        """Return a python dictionary representing the pickled data"""
        if not self.settings_pickled:
            return {}
        
        try:
            import pickle
        except ImportError:
            import cPickle as pickle
        from helpdesk.lib import b64decode
        
        try:
            return pickle.loads(b64decode(self.settings_pickled.encode('utf-8')))
        except (pickle.UnpicklingError, AttributeError):
            return {}

    @settings.setter
    def settings(self, data):
        """Set pickled settings data"""
        try:
            import pickle
        except ImportError:
            import cPickle as pickle
        from helpdesk.lib import b64encode
        
        self.settings_pickled = b64encode(pickle.dumps(data)).decode()

def create_usersettings(sender, instance, created, **kwargs):
    """Helper function to create UserSettings instances as required"""
    if created:
        UserSettings.objects.get_or_create(user=instance)

models.signals.post_save.connect(create_usersettings, sender=settings.AUTH_USER_MODEL)

class IgnoreEmail(models.Model):
    """
    Enhanced email ignore rules with pattern matching
    """
    IGNORE_TYPES = [
        ('sender', _('Sender Address')),
        ('subject', _('Subject Line')),
        ('domain', _('Domain')),
        ('regex', _('Regular Expression')),
    ]

    # Basic Information
    name = models.CharField(
        _('Name'),
        max_length=100
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of this ignore rule')
    )
    ignore_type = models.CharField(
        _('Ignore Type'),
        max_length=20,
        choices=IGNORE_TYPES,
        default='sender',
        help_text=_('What type of matching to perform')
    )

    # Pattern Matching
    email_address = models.CharField(
        _('Pattern'),
        max_length=500,
        help_text=_('Enter a full e-mail address, domain, subject pattern, or regex. Use wildcards like *@domain.com for domains.')
    )
    case_sensitive = models.BooleanField(
        _('Case Sensitive'),
        default=False,
        help_text=_('Whether pattern matching should be case sensitive')
    )

    # Queue Assignment
    queues = models.ManyToManyField(
        'base.Queue',
        blank=True,
        help_text=_('Leave blank for this rule to apply to all queues, or select specific queues.')
    )

    # Actions
    keep_in_mailbox = models.BooleanField(
        _('Keep in Mailbox'),
        default=False,
        help_text=_('Keep emails in mailbox instead of deleting them')
    )
    create_ticket_anyway = models.BooleanField(
        _('Create Ticket Anyway'),
        default=False,
        help_text=_('Create ticket but mark as ignored (for logging purposes)')
    )
    forward_to = models.EmailField(
        _('Forward To'),
        blank=True,
        help_text=_('Forward ignored emails to this address')
    )

    # Activity Tracking
    hit_count = models.PositiveIntegerField(
        _('Hit Count'),
        default=0,
        help_text=_('Number of times this rule has matched')
    )
    last_hit = models.DateTimeField(
        _('Last Hit'),
        blank=True,
        null=True,
        help_text=_('When this rule was last triggered')
    )

    # Settings
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this ignore rule is currently active')
    )
    date = models.DateField(
        _('Date Created'),
        help_text=_('Date on which this rule was added'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Ignored e-mail address')
        verbose_name_plural = _('Ignored e-mail addresses')
        ordering = ['-hit_count', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_ignore_type_display()})'

    def queue_list(self):
        """Return a list of the queues this rule applies to"""
        queues = self.queues.all().order_by('title')
        if len(queues) == 0:
            return '*'
        else:
            return ', '.join([str(q) for q in queues])

    def test(self, email_content, subject=''):
        """Test if this rule matches the given content"""
        pattern = self.email_address
        
        if self.ignore_type == 'sender':
            test_string = email_content
        elif self.ignore_type == 'subject':
            test_string = subject
        elif self.ignore_type == 'domain':
            # Extract domain from email
            if '@' in email_content:
                test_string = email_content.split('@')[1]
            else:
                return False
        elif self.ignore_type == 'regex':
            flags = 0 if self.case_sensitive else re.IGNORECASE
            try:
                return bool(re.search(pattern, email_content, flags))
            except re.error:
                return False
        else:
            test_string = email_content

        # Handle wildcards for non-regex patterns
        if self.ignore_type != 'regex':
            if not self.case_sensitive:
                pattern = pattern.lower()
                test_string = test_string.lower()
            
            # Simple wildcard matching
            if '*' in pattern:
                parts = pattern.split('*')
                if len(parts) == 2:
                    start, end = parts
                    return test_string.startswith(start) and test_string.endswith(end)
            
            return pattern == test_string
        
        return False
