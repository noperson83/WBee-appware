# helpdesk/models/templates.py - Email Templates and Preset Replies

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class PreSetReply(models.Model):
    """
    Enhanced preset replies with better organization and templating
    """
    REPLY_TYPES = [
        ('resolution', _('Resolution Template')),
        ('update', _('Status Update')),
        ('information', _('Information Request')),
        ('escalation', _('Escalation Notice')),
        ('closure', _('Ticket Closure')),
        ('welcome', _('Welcome Message')),
        ('custom', _('Custom Template')),
    ]

    # Basic Information
    name = models.CharField(
        _('Name'),
        max_length=100,
        help_text=_('Only used to assist users with selecting a reply - not shown to the user.')
    )
    body = models.TextField(
        _('Body'),
        help_text=_('Context available: {{ ticket }} - ticket object (e.g {{ ticket.title }}); {{ queue }} - The queue; and {{ user }} - the current user.')
    )
    reply_type = models.CharField(
        _('Reply Type'),
        max_length=20,
        choices=REPLY_TYPES,
        default='custom',
        help_text=_('Category of this reply template')
    )

    # Queue Assignment
    queues = models.ManyToManyField(
        'helpdesk.Queue',
        blank=True,
        help_text=_('Leave blank to allow this reply to be used for all queues, or select those queues you wish to limit this reply to.')
    )

    # Settings
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this template is currently available for use')
    )
    is_public = models.BooleanField(
        _('Public Reply'),
        default=True,
        help_text=_('Whether replies using this template are public by default')
    )
    auto_close_ticket = models.BooleanField(
        _('Auto-close Ticket'),
        default=False,
        help_text=_('Automatically close ticket when this reply is used')
    )

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('User who created this template')
    )
    created_at = models.DateTimeField(_('Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated'), auto_now=True)

    class Meta:
        ordering = ('reply_type', 'name')
        verbose_name = _('Pre-set reply')
        verbose_name_plural = _('Pre-set replies')

    def __str__(self):
        return f'{self.get_reply_type_display()}: {self.name}'

class EmailTemplate(models.Model):
    """
    Enhanced email templates with better organization
    """
    TEMPLATE_TYPES = [
        ('new_ticket', _('New Ticket Notification')),
        ('updated_ticket', _('Ticket Updated')),
        ('resolved_ticket', _('Ticket Resolved')),
        ('closed_ticket', _('Ticket Closed')),
        ('assigned_ticket', _('Ticket Assigned')),
        ('escalated_ticket', _('Ticket Escalated')),
        ('reminder', _('Reminder/Follow-up')),
        ('satisfaction', _('Satisfaction Survey')),
        ('custom', _('Custom Template')),
    ]

    # Basic Information
    template_name = models.CharField(
        _('Template Name'),
        max_length=100
    )
    template_type = models.CharField(
        _('Template Type'),
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='custom',
        help_text=_('Purpose of this email template')
    )
    
    # Email Content
    subject = models.CharField(
        _('Subject'),
        max_length=100,
        help_text=_('This will be prefixed with "[ticket.ticket] ticket.title". We recommend something simple such as "(Updated") or "(Closed)" - the same context is available as in plain_text, below.')
    )
    heading = models.CharField(
        _('Heading'),
        max_length=100,
        help_text=_('In HTML e-mails, this will be the heading at the top of the email - the same context is available as in plain_text, below.')
    )
    plain_text = models.TextField(
        _('Plain Text'),
        help_text=_('The context available to you includes {{ ticket }}, {{ queue }}, and depending on the time of the call: {{ resolution }} or {{ comment }}.')
    )
    html = models.TextField(
        _('HTML'),
        help_text=_('The same context is available here as in plain_text, above.')
    )

    # Settings
    locale = models.CharField(
        _('Locale'),
        max_length=10,
        blank=True,
        null=True,
        help_text=_('Locale of this template.')
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this template is currently available for use')
    )

    # Queue Assignment
    queues = models.ManyToManyField(
        'helpdesk.Queue',
        blank=True,
        help_text=_('Leave blank to use for all queues, or select specific queues')
    )

    # System Fields
    created_at = models.DateTimeField(_('Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated'), auto_now=True)

    class Meta:
        ordering = ('template_type', 'template_name', 'locale')
        verbose_name = _('e-mail template')
        verbose_name_plural = _('e-mail templates')

    def __str__(self):
        return f'{self.get_template_type_display()}: {self.template_name}'

class EscalationExclusion(models.Model):
    """
    Enhanced escalation exclusions with recurring patterns
    """
    EXCLUSION_TYPES = [
        ('one_time', _('One-time Exclusion')),
        ('weekly', _('Weekly Recurring')),
        ('monthly', _('Monthly Recurring')),
        ('yearly', _('Yearly Recurring')),
    ]

    # Basic Information
    name = models.CharField(
        _('Name'),
        max_length=100
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Description of this escalation exclusion')
    )
