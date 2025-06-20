# helpdesk/models/communication.py - Follow-ups, Attachments, and Communication Models

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import os

class FollowUpManager(models.Manager):
    def private_followups(self):
        return self.filter(public=False)

    def public_followups(self):
        return self.filter(public=True)

    def recent(self, days=7):
        """Get recent follow-ups"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(date__gte=cutoff)

class FollowUp(models.Model):
    """
    Enhanced follow-up model with better categorization and tracking
    """
    FOLLOWUP_TYPES = [
        ('comment', _('Comment')),
        ('status_change', _('Status Change')),
        ('assignment', _('Assignment')),
        ('escalation', _('Escalation')),
        ('resolution', _('Resolution')),
        ('email', _('Email')),
        ('phone', _('Phone Call')),
        ('meeting', _('Meeting')),
        ('system', _('System Generated')),
    ]

    # Basic Information
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='followups',
        verbose_name=_('Ticket')
    )
    date = models.DateTimeField(
        _('Date'),
        default=timezone.now
    )
    title = models.CharField(
        _('Title'),
        max_length=200,
        blank=True,
        null=True
    )
    comment = models.TextField(
        _('Comment'),
        blank=True,
        null=True
    )
    followup_type = models.CharField(
        _('Follow-up Type'),
        max_length=20,
        choices=FOLLOWUP_TYPES,
        default='comment',
        help_text=_('Type of follow-up action')
    )

    # Visibility and User
    public = models.BooleanField(
        _('Public'),
        default=False,
        help_text=_('Public follow-ups are viewable by the submitter and all staff, but non-public follow-ups can only be seen by staff.')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('User')
    )

    # Status Change Tracking
    new_status = models.IntegerField(
        _('New Status'),
        choices=[(1, _('Open')), (2, _('Reopened')), (3, _('Resolved')), (4, _('Closed')), (5, _('Duplicate')), (6, _('On Hold')), (7, _('Pending Customer'))],
        blank=True,
        null=True,
        help_text=_('If the status was changed, what was it changed to?')
    )
    old_status = models.IntegerField(
        _('Previous Status'),
        choices=[(1, _('Open')), (2, _('Reopened')), (3, _('Resolved')), (4, _('Closed')), (5, _('Duplicate')), (6, _('On Hold')), (7, _('Pending Customer'))],
        blank=True,
        null=True,
        help_text=_('Previous status before this change')
    )

    # Time Tracking
    time_spent = models.DurationField(
        _('Time Spent'),
        blank=True,
        null=True,
        help_text=_('Time spent on this follow-up')
    )
    is_billable = models.BooleanField(
        _('Billable'),
        default=True,
        help_text=_('Whether this time should be billed to the customer')
    )

    # Email Integration
    email_message_id = models.CharField(
        _('Email Message ID'),
        max_length=255,
        blank=True,
        help_text=_('Message ID for email-based follow-ups')
    )
    email_subject = models.CharField(
        _('Email Subject'),
        max_length=255,
        blank=True
    )

    objects = FollowUpManager()

    class Meta:
        ordering = ('date',)
        verbose_name = _('Follow-up')
        verbose_name_plural = _('Follow-ups')
        indexes = [
            models.Index(fields=['ticket', 'date']),
            models.Index(fields=['public', 'date']),
        ]

    def __str__(self):
        return f'{self.title} - {self.ticket}'

    def save(self, *args, **kwargs):
        # Update ticket's modified date
        self.ticket.modified = timezone.now()
        
        # Set first response date if this is the first public follow-up
        if self.public and not self.ticket.first_response_date:
            self.ticket.first_response_date = self.date
        
        self.ticket.save()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{self.ticket.get_absolute_url()}#followup{self.id}"

class TicketChange(models.Model):
    """
    Enhanced ticket change tracking with better field mapping
    """
    followup = models.ForeignKey(
        FollowUp,
        on_delete=models.CASCADE,
        related_name='changes',
        verbose_name=_('Follow-up')
    )
    field = models.CharField(
        _('Field'),
        max_length=100
    )
    old_value = models.TextField(
        _('Old Value'),
        blank=True,
        null=True
    )
    new_value = models.TextField(
        _('New Value'),
        blank=True,
        null=True
    )
    
    # Enhanced tracking
    change_type = models.CharField(
        _('Change Type'),
        max_length=20,
        choices=[
            ('field_change', _('Field Change')),
            ('assignment', _('Assignment')),
            ('status', _('Status Change')),
            ('priority', _('Priority Change')),
        ],
        default='field_change'
    )

    class Meta:
        verbose_name = _('Ticket change')
        verbose_name_plural = _('Ticket changes')
        indexes = [
            models.Index(fields=['followup', 'field']),
        ]

    def __str__(self):
        if not self.new_value:
            return f'{self.field} removed'
        elif not self.old_value:
            return f'{self.field} set to {self.new_value}'
        else:
            return f'{self.field} changed from "{self.old_value}" to "{self.new_value}"'

def attachment_path(instance, filename):
    """Provide a file path that will help prevent files being overwritten"""
    os.umask(0)
    path = f'helpdesk/attachments/{instance.followup.ticket.ticket_for_url}/{instance.followup.id}'
    att_path = os.path.join(settings.MEDIA_ROOT, path)
    if settings.DEFAULT_FILE_STORAGE == "django.core.files.storage.FileSystemStorage":
        if not os.path.exists(att_path):
            os.makedirs(att_path, 0o777)
    return os.path.join(path, filename)

class Attachment(models.Model):
    """
    Enhanced attachment model with better file handling
    """
    followup = models.ForeignKey(
        FollowUp,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Follow-up')
    )
    file = models.FileField(
        _('File'),
        upload_to=attachment_path,
        max_length=1000
    )
    filename = models.CharField(
        _('Filename'),
        max_length=1000
    )
    mime_type = models.CharField(
        _('MIME Type'),
        max_length=255
    )
    size = models.IntegerField(
        _('Size'),
        help_text=_('Size of this file in bytes')
    )
    
    # Enhanced fields
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('User who uploaded this file')
    )
    uploaded_at = models.DateTimeField(
        _('Uploaded At'),
        auto_now_add=True
    )
    is_public = models.BooleanField(
        _('Public'),
        default=True,
        help_text=_('Whether this attachment is visible to the ticket submitter')
    )
    virus_scanned = models.BooleanField(
        _('Virus Scanned'),
        default=False,
        help_text=_('Whether this file has been scanned for viruses')
    )

    class Meta:
        ordering = ('filename',)
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    def __str__(self):
        return self.filename

    @property
    def file_size_human(self):
        """Return human-readable file size"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def is_image(self):
        """Check if attachment is an image"""
        return self.mime_type.startswith('image/')

    @property
    def is_document(self):
        """Check if attachment is a document"""
        document_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        return self.mime_type in document_types
